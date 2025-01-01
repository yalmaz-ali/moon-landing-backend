import configparser
from typing import List, Dict, Any

import requests

from person_profile import PersonProfileEntities

config = configparser.ConfigParser()

class ProxycurlAPI:
	def __init__(self):
		config.read('config.cfg')
		self.api_key = config['PROXYCURL']['API_KEY']
		self.base_url = 'https://nubela.co/proxycurl/api'
		self.version = "v2"
		self.headers = {
			'Authorization': f'{self.api_key}',
			'Accept': 'application/json',
		}

	# Search for profiles based on the user query
	async def fetch_profile_urls(self, entities: PersonProfileEntities, count: int) -> List[Dict[str, Any]]:
		"""
		Fetch profile URLs based on the user query.
		:param entities: Extracted entities from the user query
		:param count: Number of profiles to fetch
		:return: List of profile URLs
		"""
		url = f'{self.base_url}/{self.version}/search/person'
		params = {
			'country': entities.country,
			'current_role_title': entities.current_role_title,
			'past_role_title': entities.past_role_title,
			'current_company_name': entities.current_company_name,
			'past_company_name': entities.past_company_name,
			'region': entities.region,
			'city': entities.city,
			'headline': entities.headline,
			'skills': entities.skills,
			# 'page_size': entities.page_size,
			'page_size': count,
			'enrich_profiles': "skip",
			'use_cache': "if-present"
		}

		# Filter out empty string values
		params = {key: value for key, value in params.items() if value}

		try:
			response = requests.get(url, headers=self.headers, params=params)
			if response.status_code == 200:
				return response.json()['results']
			elif response.status_code == 400:
				print(response.json())
			else:
				print("Failed to fetch profiles. Please try again later.")
			return []
		except Exception as e:
			print(f"Error: {e}")
			return []

	# Fetch the full profile data from the Proxycurl API
	async def fetch_full_profile(self, profile_url: str) -> Dict[str, Any]:
		"""
		Fetch the full profile data from the Proxycurl API.
		:param profile_url: LinkedIn profile URL
		:return: Full profile data
		"""
		url = f'{self.base_url}/{self.version}/linkedin'
		params = {
			'url': profile_url,
			'skills': 'include',
			'use_cache': 'if-recent',
			'fallback_to_cache': 'on-error'
		}

		try:
			response = requests.get(url, headers=self.headers, params=params)
			if response.status_code == 200:
				return response.json()
			else:
				print(f"Failed to fetch profile data for {profile_url}.")
				return {}
		except Exception as e:
			print(f"Error: {e}")
			return {}

	async def get_credit_balance(self) -> dict:
		"""
		Fetch the credit balance from the Proxycurl API.
		:return: JSON response containing the credit balance
		"""
		url = f'{self.base_url}/credit-balance'
		try:
			response = requests.get(url, headers=self.headers)
			if response.status_code == 200:
				return response.json()
			else:
				print(f"Failed to fetch credit-balance.")
				return {}
		except Exception as e:
			print(f"Error fetching credit-balance: {e}")
			return {}

	async def get_profile_pic(self, profile_url: str) -> dict:
		"""
		Fetch the profile picture for a given LinkedIn profile URL.
		:param profile_url: LinkedIn profile URL
		:return: JSON response containing the profile picture URL
		"""
		url = f'{self.base_url}/linkedin/person/profile-picture'
		params = {
			'linkedin_person_profile_url': profile_url
		}
		try:
			response = requests.get(url, headers=self.headers, params=params)
			if response.status_code == 200:
				return response.json()
			elif response.status_code == 404:
				print(f"Profile picture not found for {profile_url}.")
			elif response.status_code == 429:
				print(f"Rate limit exceeded. Please try again later.")
			else:
				print(f"Failed to fetch profile picture for {profile_url}.")
				return {}
			return response.json()
		except Exception as e:
			print(f"Error fetching profile picture: {e}")
			return {}
