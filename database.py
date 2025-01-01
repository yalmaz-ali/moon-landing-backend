import asyncio
import configparser

from pymongo import errors as mongo_errors
from pymongo.mongo_client import MongoClient

config = configparser.ConfigParser()
config.read("config.cfg")

user_name = config["MONGODB"]["USER_NAME"]
password = config["MONGODB"]["PASSWORD"]
cluster = config["MONGODB"]["CLUSTER"]
db = config["MONGODB"]["DB"]
collection = config["MONGODB"]["COLLECTION"]

uri = f"mongodb+srv://{user_name}:{password}@{cluster}?retryWrites=true&w=majority"

class Database:
	def __init__(self):
		self.client = MongoClient(uri, serverSelectionTimeoutMS=5000)
		self.db = self.client[db]
		self.profiles_collection = self.db[collection]
		self.create_indexes()

	def create_indexes(self):
		"""
		Create MongoDB indexes for the profiles collection.
		:return: None
		"""
		# Create a unique index on the 'linkedin_profile_url' field if it doesn't already exist
		try:
			self.profiles_collection.create_index("linkedin_profile_url", unique=True)
			print("Unique index created for 'linkedin_profile_url'")
		except mongo_errors.OperationFailure as e:
			print(f"Error creating index: {e}")

	@staticmethod
	def _generate_mongo_query(entities):
		"""
		Dynamically generates a MongoDB search query for profiles based on user-extracted entities.
		:param entities: User-extracted entities
		:return: MongoDB search query
		"""
		query = {
			"$search": {
				"index": "profile_search_index",
				"compound": {
					"must": [],
					"should": []
				}
			}
		}

		# Add mandatory fields to "must"
		if entities.get("country"):
			query["$search"]["compound"]["must"].append({
				"text": {"query": entities["country"], "path": "country"}
			})

		if entities.get("city"):
			query["$search"]["compound"]["must"].append({
				"text": {"query": entities["city"], "path": "city"}
			})

		# Add skills as a compound must/should
		if entities.get("skills"):
			skill_parts = entities["skills"].split("||")
			skill_query = {
				"compound": {
					"must": [],
					"should": []
				}
			}
			for skill in skill_parts:
				if "&&" in skill:
					# Split AND conditions
					and_skills = skill.split("&&")
					for and_skill in and_skills:
						skill_query["compound"]["must"].append({
							"text": {"query": and_skill.strip(), "path": "skills"}
						})
				else:
					skill_query["compound"]["should"].append({
						"text": {"query": skill.strip(), "path": "skills"}
					})

			query["$search"]["compound"]["must"].append(skill_query)

		# Add role titles to "should"
		if entities.get("current_role_title"):
			roles = entities["current_role_title"].split("||")
			for role in roles:
				query["$search"]["compound"]["should"].append({
					"text": {"query": role.strip(), "path": ["headline", "occupation", "summary"]}
				})

		return query

	async def fetch_profiles_from_db(self, entities):
		"""
		Fetch profiles from the MongoDB database based on the extracted entities.
		:param entities: Extracted entities from the user query
		:return:
		"""
		# Create a search pipeline based on the entities extracted from the user query
		search_query = self._generate_mongo_query(entities)

		search_pipeline = [
			search_query,
			{'$limit': 100},
			{'$project':
				{
					'_id': 0,
					'relevance_score': {
						'$meta': 'searchScore'
					},
					'full_name': 1,
					'profile_pic_url': 1,
					'background_cover_image_url': 1,
					'linkedin_profile_url': 1,
					'headline': 1,
					'city': 1,
					'last_updated': 1
				}
			},
			{'$sort': {'relevance_score': -1}}
		]
		profiles = list(self.profiles_collection.aggregate(search_pipeline))
		return profiles

	async def store_profiles_in_db(self, profiles, date_time):
		"""
		Store profiles in the MongoDB database.
		:param profiles: List of profiles to store
		:param date_time: Date and time of the last update
		:return: None
		"""
		async def store_profile(profile):
			profile["last_updated"] = date_time
			try:
				self.profiles_collection.insert_one(profile)
			except mongo_errors.DuplicateKeyError:
				print(f"Profile already exists in the database: {profile['linkedin_profile_url']}")
				# skip the duplicate profile
			except Exception as e:
				print(f"Error inserting profiles: {e}")

		tasks = [store_profile(profile) for profile in profiles]
		await asyncio.gather(*tasks)

	async def update_profile_pic(self, profile_url, profile_pic_url):
		"""
		Update the profile picture URL for a given profile URL.
		:param profile_url: Profile URL to update
		:param profile_pic_url: New profile picture URL
		:return: None
		"""
		try:
			self.profiles_collection.update_one(
				{"linkedin_profile_url": profile_url},
				{"$set": {"profile_pic_url": profile_pic_url}}
			)
		except Exception as e:
			print(f"Error updating profile picture for {profile_url}: {e}")

