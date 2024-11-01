import json
import os
from src.github_handler import GitHubRepo
from src.llm_handler import LLMAssessor
from src.format_checker import FormatValidator
from src.markdown_generator import MarkdownReport
from src.config import MAX_FORMAT_ATTEMPTS

def load_rubric():
    """
    Load rubric from the JSON file in the data directory.
    """
    print("loading rubric")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    rubric_path = os.path.join(project_root, 'data', 'rubric.json')
    
    try:
        with open(rubric_path, 'r') as f:
            rubric_data = json.load(f)
            return rubric_data['rubric_items']
    except Exception as e:
        raise Exception(f"Failed to load rubric: {str(e)}")

def assess_repository(repo_url: str) -> str:
    """
    Main function to assess a GitHub repository against the rubric.
    """
    print("begininng to asses repo")
    try:
        # Initialize components
        repo = GitHubRepo(repo_url)
        assessor = LLMAssessor()
        validator = FormatValidator()
        report_generator = MarkdownReport()
        print("components initialized")

        # Load rubric directly from JSON file
        rubric_items = load_rubric()
        
        results = []
        
        # Process each rubric item
        for item in rubric_items:
            # Create assessment prompt based on rubric item structure
            assessment = assessor.assess_item(
                repo, 
                {
                    'title': item['title'],
                    'criteria': item['criteria'],
                    'range': item['range'],
                    'values': item['values']
                }
            )
            
            # Validate and potentially fix format
            attempts = 0
            while attempts < MAX_FORMAT_ATTEMPTS:
                if validator.is_valid(assessment):
                    break
                assessment = assessor.fix_format(assessment)
                attempts += 1
            
            if attempts == MAX_FORMAT_ATTEMPTS:
                assessment = {
                    "score": 0, 
                    "reason": "Manual review needed",
                    "range": item['range'],
                    "values": item['values']
                }
                
            results.append({
                "item": item,
                "assessment": assessment
            })

            # If this is a critical item and score is 0, stop assessment
            if item.get('critical', False) and assessment['score'] == 0:
                results.append({
                    "item": "CRITICAL FAILURE",
                    "assessment": {
                        "score": 0,
                        "reason": f"Critical item '{item['title']}' failed. Overall grade is 0."
                    }
                })
                break

        # Generate final report
        return report_generator.generate(results)

    except Exception as e:
        return f"Error during assessment: {str(e)}"

if __name__ == "__main__":
    repo_url = "https://github.com/Marziia/us-presidential-election-analysis/issues/1"
    report = assess_repository(repo_url)
    print(report)