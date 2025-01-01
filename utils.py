import asyncio
import datetime
import json
import threading
from typing import List, Dict, Any

from pydantic import BaseModel

from person_profile import PersonProfileEntities


class PersonProfile(BaseModel):
	full_name: str
	profile_pic_url: str
	profile_url: str
	relevance_score: float

class UserQuery(BaseModel):
	prompt: str

class Utils:
	def __init__(self, proxycurl, llm_ner, database):
		self.proxycurl = proxycurl
		self.llm_ner = llm_ner
		self.database = database
		self.loop = asyncio.new_event_loop()
		self.thread = threading.Thread(target=self.start_loop, daemon=True)
		self.thread.start()

	def start_loop(self):
		asyncio.set_event_loop(self.loop)
		self.loop.run_forever()

	@staticmethod
	def is_fresh(profile: Dict[str, Any]) -> bool:
		"""
		Check if the profile is fresh based on the last updated date (within 30 days).
		:param profile: Profile data
		:return: True if fresh, False otherwise
		"""
		last_updated = profile.get("last_updated")
		status = last_updated > datetime.datetime.now() - datetime.timedelta(days=30)
		return status

	@staticmethod
	def is_valid_query(entities):
		"""
		Check if the extracted entities are valid.
		:param entities: Extracted entities
		:return: True if valid, False otherwise
		"""
		country = entities.get("country") or None
		city = entities.get("city") or None
		skills = entities.get("skills") or None
		current_role_title = entities.get("current_role_title") or None

		if country is None or city is None or skills is None or current_role_title is None:
			return False

		return True

	def extract_entities(self, query: str) -> dict:
		"""
		Extract entities from the user query using the LLM NER model.
		:param query: User query
		:return: Extracted entities
		"""
		future = asyncio.run_coroutine_threadsafe(self.llm_ner.extract_entities(query), self.loop)
		entities = future.result()

		return json.loads(entities)

	async def fetch_save_new_profiles(self, entities: dict, count: int = 5) -> List[Dict[str, Any]]:
		"""
		Fetch new profiles from the Proxycurl API based on the extracted entities.
		:param entities: Extracted entities
		:param count: Number of profiles to fetch
		:return: List of profiles
		"""
		entities = PersonProfileEntities(**entities)
		profiles = await self.proxycurl.fetch_profile_urls(entities, count)
		print(profiles)
		full_profiles = []
		for profile in profiles:
			# Fetch the full profile data from the Proxycurl API
			print(profile['linkedin_profile_url'])
			full_profile = await self.proxycurl.fetch_full_profile(profile['linkedin_profile_url'])
			if not full_profile:
				continue
			full_profile['linkedin_profile_url'] = profile['linkedin_profile_url']
			full_profiles.append(full_profile)

		# Store the new profiles in the database
		await self.database.store_profiles_in_db(full_profiles, datetime.datetime.now())

		return full_profiles

	async def update_and_check_freshness(self, profiles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
		"""
		Update and check the freshness of the profiles.
		:param profiles: List of profiles
		:return: List of updated profiles
		"""
		async def update_profile(profile):
			if self.is_fresh(profile):
				return profile
			else:
				enriched_profile = await self.proxycurl.fetch_full_profile(profile['linkedin_profile_url'])
				await self.database.store_profiles_in_db([enriched_profile], datetime.datetime.now())
				return enriched_profile

		tasks = [update_profile(profile) for profile in profiles]
		fresh_profiles = await asyncio.gather(*tasks)
		return fresh_profiles


	async def score_profiles(self, profiles: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
		# async with httpx.AsyncClient() as client:
		#     response = await client.post(RELEVANCE_MODEL_URL, json={"profiles": profiles, "query": query})
		#     scored_profiles = response.json()
		return profiles

