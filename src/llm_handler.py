from src.config import GITHUB_TOKEN, ENDPOINT, RESPONSE_FORMAT
from openai import OpenAI

class LLMAssessor:
    def __init__(self):
            self.client = OpenAI(
            base_url=ENDPOINT,
            api_key=GITHUB_TOKEN,
        )
            self.model_name = "gpt-4o"

    def assess_item(self, repo, rubric_item):
        prompt = f"""
        Please visit this GitHub repository: {repo.repo_url}
        Browse through the repository contents, including the code, README, and other relevant files.
        Then assess it against this rubric item:
        
        Rubric Item: {rubric_item['title']}
        Criteria: {rubric_item['criteria']}
        
        Provide your assessment in the following format:
        {RESPONSE_FORMAT}
        
        Be specific in your reasoning and ensure your response strictly follows the JSON format.
        Base your assessment only on what you can see in the repository.
        """

        try:
            print("trying first response")
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are an expert code reviewer who provides detailed assessments of GitHub repositories."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            print("about to return first response")
            print(response.choices[0].message.content.strip())
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error in assessment: {str(e)}")
            return None

    def fix_format(self, assessment):
        print("fixing formating")
        prompt = f"""
        The following assessment needs to be reformatted to match the required format:
        
        Original assessment:
        {assessment}
        
        Required format:
        {RESPONSE_FORMAT}
        
        Please reformat the assessment to match the required format exactly. 
        Ensure all fields are present and valid (score between 0-100, confidence between 0-1).
        Return only the reformatted JSON, nothing else.
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a formatting assistant that ensures responses match the required JSON structure."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # lower temp
                max_tokens=300
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error in format fixing: {str(e)}")
            return None