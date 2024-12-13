import json
import os
from langchain_anthropic import ChatAnthropic 
from langchain_core.documents import Document
import requests
import base64
import fnmatch
from typing import Dict, List, Any
from datetime import datetime
import anthropic
from src.config import GITHUB_API_TOKEN, ANTHROPIC_API_TOKEN

class RepoGrader:
    def __init__(self, github_token: str, anthropic_api_key: str, rubric_path: str):
        self.github_token = github_token
        self.llm = ChatAnthropic(
            model="claude-3-opus-20240229",
            anthropic_api_key=anthropic_api_key,
            temperature=0.3
        )
        with open(rubric_path, 'r') as f:
            self.rubric = json.load(f)['rubric_items']

    def get_repo_contents(self, owner: str, repo: str) -> List[Dict[str, Any]]:
        """Fetch all contents from a GitHub repository"""
        url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/main?recursive=1"
        headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github+json"
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()["tree"]
        else:
            raise ValueError(f"Error fetching repo contents: {response.status_code}")

    def fetch_file_content(self, url: str) -> str:
        """Fetch and decode content of a single file with robust encoding handling"""
        headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github+json"
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            content = response.json()["content"]
            decoded_bytes = base64.b64decode(content)
            
            # Try different encodings
            encodings = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
            for encoding in encodings:
                try:
                    return decoded_bytes.decode(encoding)
                except UnicodeDecodeError:
                    continue
                    
            # If no encoding worked, return a placeholder message
            return "[File content could not be decoded - binary or unsupported encoding]"
        return ""

    def create_grading_prompt(self, rubric_item: Dict[str, Any], repo_files: Dict[str, str]) -> str:
        """Create a prompt for grading a specific rubric item"""
        prompt_template = """
        You are grading a GitHub repository according to this rubric item:
        
        Title: {title}
        Criteria: {criteria}
        Possible scores: {values}
        Maximum points: {max_points}
        Is critical: {is_critical}
        
        Here are all the files from the repository:
        
        {files}
        
        Important grading instructions:
        1. Consider ALL files when grading, not just the README. Many projects put their main content in paper.qmd, paper.Rmd, paper.pdf, or similar files.
        2. For citations and references, check ALL document files (md, qmd, Rmd, pdf, tex), not just the README.
        3. For code-related criteria, focus on .R, .py and similar files.
        4. Grade based on the overall repository content, not any single file.
        
        Please grade this repository for this rubric item. Provide:
        1. A numerical grade based on the possible scores (must be one of the exact scores listed above)
        2. A detailed explanation of why you assigned this grade, mentioning which files contained relevant content
        
        Format your response exactly as:
        GRADE: [numerical grade]
        EXPLANATION: [your detailed explanation]
        """
        
        files_content = "\n\n=== FILE: ".join([f"{path}\n{content}" 
                                           for path, content in repo_files.items()])
        
        return prompt_template.format(
            title=rubric_item["title"],
            criteria=rubric_item["criteria"],
            values=json.dumps(rubric_item["values"], indent=2),
            max_points=rubric_item["range"]["max"],
            is_critical=rubric_item.get("critical", False),
            files="=== FILE: " + files_content
        )

    def analyze_repo(self, owner: str, repo: str) -> Dict[str, Any]:
        """Analyze repository contents and grade according to rubric"""
        contents = self.get_repo_contents(owner, repo)
        repo_files = {}
        
        # Fetch contents of relevant files
        for file in contents:
            if file["type"] == "blob":
                if any(file["path"].endswith(ext) for ext in ['.md', '.qmd', '.py', '.R', '.r', '.Rmd', '.json', '.txt']):
                    repo_files[file["path"]] = self.fetch_file_content(file["url"])

        grades = {}
        explanations = {}
        
        # Grade each rubric item
        for item in self.rubric:
            try:
                print(f"grading reubric item {item['title']}")
                prompt = self.create_grading_prompt(item, repo_files)
                response = self.llm.invoke(prompt)
                
                grade_response = self.parse_grading_response(response, item)
                grades[item["title"]] = grade_response["grade"]
                explanations[item["title"]] = grade_response["explanation"]
            except Exception as e:
                print(f"Error grading {item['title']}: {str(e)}")
                grades[item["title"]] = 0
                explanations[item["title"]] = f"Error during grading: {str(e)}"

        return {
            "grades": grades,
            "explanations": explanations,
            "total_score": self.calculate_total_score(grades)
        }

    def parse_grading_response(self, response: str, rubric_item: Dict[str, Any]) -> Dict[str, Any]:
        """Parse the LLM's grading response"""
        content = response.content if hasattr(response, 'content') else str(response)
        lines = content.strip().split('\n')
        grade = 0
        explanation = ""
        
        for line in lines:
            if line.startswith("GRADE:"):
                try:
                    grade = float(line.replace("GRADE:", "").strip())
                except:
                    grade = 0
            elif line.startswith("EXPLANATION:"):
                explanation = line.replace("EXPLANATION:", "").strip()
                
        # Validate grade is within range
        grade = max(rubric_item["range"]["min"], 
                   min(rubric_item["range"]["max"], grade))
                
        return {
            "grade": grade,
            "explanation": explanation
        }

    def calculate_total_score(self, grades: Dict[str, float]) -> float:
        """Calculate the total score based on individual grades"""
        total = 0
        max_possible = 0
        
        for item in self.rubric:
            max_possible += item["range"]["max"]
            if item["title"] in grades:
                if item.get("critical", False) and grades[item["title"]] == 0:
                    return 0  # Failed a critical item
                total += grades[item["title"]]
                
        return (total / max_possible) * 100 if max_possible > 0 else 0

    def generate_markdown_report(self, owner: str, repo: str, results: Dict[str, Any]) -> str:
        """Generate a detailed markdown report of the grading results"""
        report = f"""# Grading Report for {owner}/{repo}
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Overall Score: {results['total_score']:.2f}%

## Detailed Breakdown

"""
        # Group items by category (critical vs non-critical)
        critical_items = []
        regular_items = []
        
        for item in self.rubric:
            title = item["title"]
            if title in results["grades"]:
                entry = {
                    "title": title,
                    "grade": results["grades"][title],
                    "max": item["range"]["max"],
                    "explanation": results["explanations"][title],
                    "critical": item.get("critical", False)
                }
                if entry["critical"]:
                    critical_items.append(entry)
                else:
                    regular_items.append(entry)

        # Add critical items first
        if critical_items:
            report += "### Critical Items\n\n"
            for item in critical_items:
                report += f"#### {item['title']} ({item['grade']}/{item['max']} points)\n"
                report += f"*{item['explanation']}*\n\n"

        # Add regular items
        report += "### Regular Items\n\n"
        for item in regular_items:
            report += f"#### {item['title']} ({item['grade']}/{item['max']} points)\n"
            report += f"*{item['explanation']}*\n\n"

        return report

def main():
    # Load environment variables
    github_token = GITHUB_API_TOKEN
    anthropic_api_key = ANTHROPIC_API_TOKEN
    
    if not github_token or not anthropic_api_key:
        raise ValueError("Please set GITHUB_TOKEN and ANTHROPIC_API_KEY environment variables")

    # Initialize grader
    grader = RepoGrader(
        github_token=github_token,
        anthropic_api_key=anthropic_api_key,
        rubric_path="src/data/rubric.json"
    )

    # Get repository details from command line
    import argparse
    parser = argparse.ArgumentParser(description="Grade a GitHub repository")
    parser.add_argument("url", help="GitHub repository URL")
    args = parser.parse_args()

    # Parse GitHub URL
    parts = args.url.strip("/").split("/")
    owner = parts[-2]
    repo = parts[-1]

    # Grade repository
    results = grader.analyze_repo(owner, repo)
    
    # Generate report
    report = grader.generate_markdown_report(owner, repo, results)
    
    # Save report
    report_filename = f"grading_report_{owner}_{repo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(report_filename, 'w') as f:
        f.write(report)
    
    print(f"Grading complete! Report saved to {report_filename}")

if __name__ == "__main__":
    main()