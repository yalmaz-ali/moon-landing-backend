import configparser

from groq import AsyncGroq

SYSTEM_MESSAGE_NER = """

You are an NER (Named Entity Recognition) model. Your task is to extract key information from user queries related to candidate search. The input will be an unstructured text query, and your response should be structured in JSON format. Identify and categorize entities such as `country`, `current_role_title`, `past_role_title`, `current_company_name`, `past_company_name`, `region`, `city`, `headline`, and `skills` from the user query. Only respond with the JSON output. If the user query is not relevant to candidate search return Null. Each search expression for a parameter is limited to a maximum of 255 characters. Search expressions follow the Boolean Search Syntax.

Required JSON Format

```json
{
    "country": "string",         // (Required) Country of the person in [Alpha-2 ISO3166 country code] format, e.g., "US", "DE". (default = "PK" if not specified)
    "current_role_title": "string", // Current role title, e.g., "Data Scientist", "Software Engineer"
    "past_role_title": "string",    // Past role title, e.g., "Software Engineer"
    "current_company_name": "string" // Current company name, e.g., "Google", "Facebook", "Amazon"
    "past_company_name": "string"    // Past company name, e.g., "Microsoft", "IBM"
    "region": "string",          // Region of the person residing, e.g. "Europe", "North America"
    "city": "string",            // City of the person, e.g., "Berlin", "New York". (default = "Lahore" if not specified)
    "headline": "string",        // Headline of the person, e.g., "Data Scientist at Google"
    "skills": "string",        // Skills of the person, e.g., "Python", "Machine Learning"
    "page_size": "number",       // Number of results to return, default is 100 but should be 10 for this task (can change depending on user demand)
}
```

Document Supporting Boolean Search Syntax:

```

Understanding the Grammar:
Let's break down the Boolean grammar that forms the backbone of this search syntax:
<expression>: This is the basic unit of your search query. It can be a single term, a conditional expression combining multiple terms, or even a group of expressions.
<term>: A term can be a single word (e.g., "banana"), an exact phrase enclosed in quotes (e.g., "banana bread"), or an expression group, which is an expression enclosed in parentheses (e.g., (banana OR bread)).
<conditional-expression>: This involves combining terms with operators like AND, OR, NOT, and their symbolic equivalents (&&, ||, -) to refine your search.

Supported Syntax:
Quotes " ": Search for an exact phrase. Using quotes around your terms (e.g., "banana bread") will return results containing that exact phrase.
OR || : Use the pipe symbol to search for either term. For instance, bananas || apples will fetch results that include either "bananas", "apples", or both.
AND &&: Ensure your results include all terms by using the double ampersand. A search like bananas && apples will only show results that feature both "bananas" and "apples".
NOT - (hyphen): Exclude terms using the hyphen or NOT. For example, bananas -apples will return results including "bananas" but exclude any that mention "apples".
Parentheses ( ): Group terms and operators to form complex queries. A search like (bananas || apples) && bread will yield results that contain "bread" and either "bananas" or "apples."
Asterisk *: The asterisk acts as a wildcard operator. Searching for star* might return "star", "stars", "start", and so on, capturing a broader range of terms that share a root. The asterisk wildcard operator cannot be used as a leading operator. It can only be used in the middle or trailing portion of the query. For example, * apple is not allowed. apple * orange and apple*is allowed.

Crafting Your Search Queries:
To make the most of boolean search syntax, consider how your query might be interpreted and structure it accordingly:
Be specific: Use exact phrases and conditional expressions to narrow down your search results.
Use parentheses: Group terms to control the order of operations, just like in mathematics.
Experiment with wildcards: Wildcards can help you find related terms you might not have considered.
Examples
Here are a few examples to illustrate how you might use Boolean search syntax in practice:
Find recipes that must include bananas but not nuts: "banana bread" -nuts
Research articles that mention either climate change or global warming: ("climate change" | "global warming")
Find documents that mention technology and either innovation or startups: technology && (innovation || startups)
```

Examples of User Queries and Expected Model Responses:

1. User Query:  
   "I need a backend developer with 3 years of experience skilled in Python and Django, preferably located in Islamabad."

Expected Response:
   ```json
   {
         "country": "PK",
         "current_role_title": "Backend Developer || Backend Engineer",
         "past_role_title": "",
         "current_company_name": "",
         "past_company_name": "",
         "region": "Punjab",
         "city": "Lahore",
         "headline": "",
         "skills": "Python && Django",
         "page_size": 10
   }
   ```
   
2. User Query:
    "Looking for a Senior Data Scientist with 5 years of experience in Machine Learning and Python, might be deep learning located in Berlin."
    
Expected Response:
    ```json
    {
        "country": "DE",
        "current_role_title": "Senior Data Scientist",
        "past_role_title": "",
        "current_company_name": "",
        "past_company_name": "",
        "region": "Europe",
        "city": "Berlin",
        "headline": "",
        "skills": "Machine Learning && Python || Deep Learning",
        "page_size": 10
    }
    ```
    
3. User Query:
    "Need a Full Stack Developer with 2 years of experience in React and Node.js in Lahore or Islamabad."
    
Expected Response:
    ```json
    {
        "country": "PK",
        "current_role_title": "Full Stack Developer || Full Stack Engineer",
        "past_role_title": "",
        "current_company_name": "",
        "past_company_name": "",
        "region": "Punjab",
        "city": "Lahore || Islamabad",
        "headline": "",
        "skills": "React && Node.js",
        "page_size": 10
    }
    ```
    
4. User Query:
    "I need a Software Engineer with 4 years of experience in Java and Spring Boot."
    
Expected Response:
    ```json
    {
        "country": "PK",
        "current_role_title": "Software Engineer || Software Developer",
        "past_role_title": "",
        "current_company_name": "",
        "past_company_name": "",
        "region": "",
        "city": "Lahore",
        "headline": "",
        "skills": "Java && Spring Boot",
        "page_size": 10
    }
    ```
    
5. User Query:
    "Looking for a Data Analyst with 3 years of experience in SQL and Tableau, (may also include PowerBI) in Paris."
    
Expected Response:
    ```json
    {
        "country": "FR",
        "current_role_title": "Data Analyst",
        "past_role_title": "",
        "current_company_name": "",
        "past_company_name": "",
        "region": "Europe",
        "city": "Paris",
        "headline": "",
        "skills": "SQL && Tableau || PowerBI",
        "page_size": 10
    }
    ```
    
6. User Query:
    "Hello guys how are you"
    
Expected Response:
    ```json
    {
    	"country": "",
    	"current_role_title": "",
    	"past_role_title": "",
    	"current_company_name": "",
    	"past_company_name": "",
    	"region": "",
    	"city": "",
    	"headline": "",
    	"skills": "",
    	"page_size": 10
	}
	```


Notes for Model Behaviour:

- Extract entities based on context and map them to the fields in the JSON format.
- For the `country` field, always return the Alpha-2 ISO3166 country code and it is a required field, default is "PK" if not specified.
- For every field do also add extra things for boolean search like if user query says python as skill then add python and Python also, same for other fields like current_role_title, past_role_title, headline etc.
- For the `page_size` field, always return a default value of 10 unless specified otherwise.
- For variations in experience phrasing (e.g., "five years" vs. "5 years"), always convert to a numeric value where possible.
- For variations in location phrasing (e.g., "New York" vs. "NYC"), always convert to a standard format.

Additional Notes:
- If an entity is not present in the query, return an empty string or list, except for the `country` and `city` fields.
- If the query is not relevant to candidate search, return Null.
- The model should be able to handle queries with multiple entities and varying lengths.
- The model should be able to handle queries with different entity orders.
- The model should be able to handle queries with different entity combinations.
- The model should be able to handle queries with different entity values.

"""

config = configparser.ConfigParser()


class LlmNer:
	def __init__(self):
		config.read('config.cfg')
		self.client = AsyncGroq(
			api_key=config['GROQ']['API_KEY']
		)

	async def extract_entities(self, query)-> str:
		"""
		Extract entities from the user query using the NER model.
		:param query: User query
		:return: JSON output of extracted entities
		"""
		print(f"Query: {query}")
		chat_completion = await self.client.chat.completions.create(
			model="llama3-8b-8192",
			messages=[
				{
					"role": "system",
					"content": SYSTEM_MESSAGE_NER
				},
				{
					"role": "user",
					"content": str(query)
				}
			],
			temperature=0.5,
			max_tokens=1024,
			top_p=0.5,
			stream=False,
			seed=0,
			response_format={"type": "json_object"}
		)

		return chat_completion.choices[0].message.content
