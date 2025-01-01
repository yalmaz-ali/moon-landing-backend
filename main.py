import asyncio
import configparser

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from database import Database
from llm_ner import LlmNer
from proxy_curl import ProxycurlAPI
from utils import UserQuery, Utils

# Load the configuration file
config = configparser.ConfigParser()
config.read('config.cfg')

# Create a new FastAPI instance
app = FastAPI()
proxycurl = ProxycurlAPI()
llm_ner = LlmNer()
database = Database()
utils = Utils(proxycurl, llm_ner, database)

@app.post("/search-profiles")
async def search_profiles(user_query: UserQuery):
	"""
	Search for profiles based on the user query.
	:param user_query: User query
	:return: List of profiles
	"""
	# Step 1: Extract entities from the query using NER model
	entities = utils.extract_entities(user_query.prompt)
	if not utils.is_valid_query(entities):
		raise HTTPException(status_code=400, detail="Your query is invalid. Please provide a valid query.")
	# Step 2: Check for matching profiles in the database
	profiles = await database.fetch_profiles_from_db(entities)
	if profiles:
		# Step 3: Score profiles for relevance
		profiles = await utils.score_profiles(profiles, user_query.prompt)
		profiles = [p for p in profiles if p.get("relevance_score") > 0.8]

		# Step 4: Fetch new profiles 30% of profiles from Proxycurl if necessary
		count = int(len(profiles) * 0.3)
		new_profiles = await utils.fetch_save_new_profiles(entities, count if count > 5 else 5)
		profiles.extend(new_profiles)
	else:
		# If no profiles are found in DB, fetch from Proxycurl directly
		profiles  = await utils.fetch_save_new_profiles(entities)
	if not profiles:
		raise HTTPException(status_code=404, detail="No profiles found for the given query.")

	# Step 5: Store unique profiles in DB with date and time
	# await database.store_profiles_in_db(profiles, date_time=datetime.datetime.now())

	# Step 6: Re-fetch profiles from DB after updates
	profiles = await database.fetch_profiles_from_db(entities)

	# Step 7: Check freshness and enrich if necessary
	profiles = await utils.update_and_check_freshness(profiles)

	# # Step 8: Score profiles for relevance again
	profiles = await utils.score_profiles(profiles, user_query.query)

	# Step 9: Return profiles with limited info for display
	return profiles


@app.get("/credit-balance")
async def get_credit_balance():
	"""
	Get the credit balance from the Proxycurl API.
	:return: Credit balance
	"""
	# Get the credit balance from the Proxycurl API
	credit_balance = await proxycurl.get_credit_balance()
	if not credit_balance:
		raise HTTPException(status_code=500, detail="Failed to fetch credit balance.")
	return JSONResponse(content=credit_balance)

@app.get("/get-profile-pic")
async def get_profile_pic(profile_url: str):
	"""
	Get the profile picture URL for a given profile URL.
	:param profile_url: Profile URL
	:return: Profile picture URL
	"""
	# Get the profile pic from the Proxycurl API
	profile_pic = await proxycurl.get_profile_pic(profile_url)
	if not profile_pic:
		raise HTTPException(status_code=500, detail="Failed to fetch profile picture.")
	elif profile_pic.get("code") == 404:
		raise HTTPException(status_code=404, detail=profile_pic["description"])
	elif profile_pic.get("error"):
		raise HTTPException(status_code=500, detail=profile_pic["error"])

	# update the profile_pic_url in the profile object also in another thread
	asyncio.create_task(database.update_profile_pic(profile_url, profile_pic.get("tmp_profile_pic_url")))

	return JSONResponse(content=profile_pic)
