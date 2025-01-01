from pydantic import BaseModel


class PersonProfileEntities(BaseModel):
	country: str
	current_role_title: str = None
	past_role_title: str = None
	current_company_name: str = None
	past_company_name: str = None
	region: str = None
	city: str = None
	headline: str = None
	skills: str = None
	page_size: int = 10
