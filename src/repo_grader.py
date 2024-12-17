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
        """Fetch and decode content of a single file"""
        headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github+json"
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            content = response.json()["content"]
            try:
                return base64.b64decode(content).decode('utf-8')
            except UnicodeDecodeError:
                return "[Binary file content]"
        return ""

    def preprocess_repo_content(self, repo_files: Dict[str, str]) -> Dict[str, Dict[str, Any]]:
        """Group repository content by type, storing only metadata for data files"""
        processed = {
            'documentation': {},  # .md, .qmd, .Rmd, etc
            'code': {},          # .py, .R, etc
            'data_metadata': {}, # Only metadata for data files
            'other': {}          # Everything else
        }
        
        for path, content in repo_files.items():
            if not content:
                continue
                
            ext = path.lower().split('.')[-1]
            
            if ext in ['md', 'qmd', 'rmd', 'txt']:
                processed['documentation'][path] = content
            elif ext in ['py', 'r', 'ipynb']:
                processed['code'][path] = content
            elif ext in ['csv', 'parquet', 'json', 'xlsx', 'xls', 'dta', 'sav', 'dat']:
                # Store only metadata for data files
                processed['data_metadata'][path] = {
                    'path': path,
                    'size': len(content),
                    'extension': ext,
                    'directory': '/'.join(path.split('/')[:-1]) or '.'
                }
            else:
                processed['other'][path] = f"[File: {path}]"
                
        return processed

    def analyze_repo(self, owner: str, repo: str) -> Dict[str, Any]:
        """Analyze repository with optimized LLM usage"""
        print(f"Fetching repository contents for {owner}/{repo}...")
        contents = self.get_repo_contents(owner, repo)
        repo_files = {}
        
        print("Processing files...")
        for file in contents:
            if file["type"] == "blob":
                repo_files[file["path"]] = self.fetch_file_content(file["url"])

        processed_content = self.preprocess_repo_content(repo_files)
        
        print("Starting grading process...")
        results = self.batch_grade_rubric(processed_content)
        
        return results

    def format_rubric_item(self, item: Dict[str, Any]) -> str:
        """Format a rubric item for inclusion in prompts"""
        return (f"Title: {item['title']}\n"
                f"Criteria: {item['criteria']}\n"
                f"Possible scores: {item['values']}\n"
                f"Maximum points: {item['range']['max']}\n"
                f"Is critical: {item.get('critical', False)}")

    def batch_grade_rubric(self, processed_content: Dict[str, Dict[str, str]]) -> Dict[str, Any]:
        """Grade rubric items in strategic batches"""
        results = {
            'grades': {},
            'explanations': {}
        }
        
        # First batch: Critical requirements
        print("Grading critical requirements...")
        critical_items = [item for item in self.rubric if item.get('critical', False)]
        critical_results = self.grade_critical_batch(critical_items, processed_content)
        results['grades'].update(critical_results['grades'])
        results['explanations'].update(critical_results['explanations'])
        
        if any(grade == 0 for grade in critical_results['grades'].values()):
            print("Critical requirement failed - stopping grading process")
            return results
            
        # Second batch: Document structure and content
        print("Grading document structure and content...")
        doc_items = [item for item in self.rubric 
                    if not item.get('critical', False) and 
                    item['title'].lower() in ['abstract', 'introduction', 'data', 'results', 
                                            'discussion', 'title', 'prose', 'author, date, and repo']]
        doc_results = self.grade_document_batch(doc_items, processed_content)
        results['grades'].update(doc_results['grades'])
        results['explanations'].update(doc_results['explanations'])
        
        # Third batch: Technical implementation
        print("Grading technical implementation...")
        tech_items = [item for item in self.rubric 
                     if not item.get('critical', False) and 
                     item['title'].lower() in ['model', 'simulation', 'tests-simulation', 
                                             'tests-actual', 'reproducible workflow']]
        tech_results = self.grade_technical_batch(tech_items, processed_content)
        results['grades'].update(tech_results['grades'])
        results['explanations'].update(tech_results['explanations'])
        
        # Fourth batch: Everything else
        remaining_items = [item for item in self.rubric 
                         if item['title'] not in results['grades']]
        if remaining_items:
            print("Grading remaining items...")
            remaining_results = self.grade_remaining_batch(remaining_items, processed_content)
            results['grades'].update(remaining_results['grades'])
            results['explanations'].update(remaining_results['explanations'])
        
        # Calculate total score
        results['total_score'] = self.calculate_total_score(results['grades'])
        
        return results

    def grade_critical_batch(self, items: List[Dict], 
                           content: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Grade critical pass/fail requirements"""
        prompt = """You are evaluating critical pass/fail requirements for an academic paper.
These requirements MUST be met for the paper to pass.

Critical requirements to evaluate:
{requirements}

Repository content:

Documentation files:
{docs}

Code files:
{code}

Data files present:
{data_files}

Evaluate each requirement carefully, looking for clear evidence in ANY file.
Consider code comments, documentation, and all relevant text.

For each requirement, provide your response in exactly this format:
ITEM: [requirement title]
GRADE: [0 or 1]
EXPLANATION: [detailed explanation with specific evidence]
END_ITEM"""
        
        formatted_requirements = "\n\n".join(self.format_rubric_item(item) for item in items)
        
        response = self.llm.invoke(prompt.format(
            requirements=formatted_requirements,
            docs="\n\n".join(f"File: {path}\nContent:\n{content}" 
                            for path, content in content['documentation'].items()),
            code="\n\n".join(f"File: {path}\nContent:\n{content}" 
                            for path, content in content['code'].items()),
            data_files=json.dumps(content['data_metadata'], indent=2)
        ))
        
        return self.parse_batch_response(response.content)

    def grade_document_batch(self, items: List[Dict], 
                           content: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Grade document structure and content items"""
        prompt = """You are evaluating the structure and content of an academic paper.
Focus on writing quality, organization, and completeness of required sections.

Items to evaluate:
{items}

Document files:
{docs}

For each item, provide your response in exactly this format:
ITEM: [item title]
GRADE: [numerical grade based on item's range]
EXPLANATION: [detailed explanation with specific evidence]
END_ITEM"""
        
        formatted_items = "\n\n".join(self.format_rubric_item(item) for item in items)
        
        response = self.llm.invoke(prompt.format(
            items=formatted_items,
            docs="\n\n".join(f"File: {path}\nContent:\n{content}" 
                            for path, content in content['documentation'].items())
        ))
        
        return self.parse_batch_response(response.content)

    def grade_technical_batch(self, items: List[Dict], 
                         content: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Grade technical implementation items with size management"""
        # Only include .py and .R files
        main_code = {k: v for k, v in content['code'].items() 
                    if k.lower().endswith(('.r', '.py'))}
        
        # Split into multiple batches if needed
        results = {'grades': {}, 'explanations': {}}
        code_items = list(main_code.items())
        batch_size = 3  # Process 3 files at a time
        
        for i in range(0, len(code_items), batch_size):
            batch_files = dict(code_items[i:i + batch_size])
            
            prompt = """You are evaluating the technical implementation of an academic paper.
Focus on code quality, testing, reproducibility, and technical completeness.

Items to evaluate:
{items}

Code files (batch {batch_num} of {total_batches}):
{code}

Data files present in repository (metadata only):
{data_metadata}

For each item, provide your response in exactly this format:
ITEM: [item title]
GRADE: [numerical grade based on item's range]
EXPLANATION: [detailed explanation with specific evidence]
END_ITEM"""
            
            formatted_items = "\n\n".join(self.format_rubric_item(item) for item in items)
            total_batches = (len(code_items) + batch_size - 1) // batch_size
            current_batch = i // batch_size + 1
            
            response = self.llm.invoke(prompt.format(
                items=formatted_items,
                batch_num=current_batch,
                total_batches=total_batches,
                code="\n\n".join(f"File: {path}\nContent:\n{content}" 
                                for path, content in batch_files.items()),
                data_metadata=json.dumps(content['data_metadata'], indent=2)
            ))
            
            batch_results = self.parse_batch_response(response.content)
            
            # For first batch, use the grades as is
            if i == 0:
                results = batch_results
            # For subsequent batches, update grades if they're higher
            else:
                for title in batch_results['grades']:
                    if title not in results['grades'] or batch_results['grades'][title] > results['grades'][title]:
                        results['grades'][title] = batch_results['grades'][title]
                        results['explanations'][title] = batch_results['explanations'][title]
        
        return results

    def grade_remaining_batch(self, items: List[Dict], 
                            content: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Grade remaining rubric items"""
        prompt = """Grade these remaining rubric items considering all repository content.

Items to evaluate:
{items}

Repository structure:
{repo_structure}

For each item, provide your response in exactly this format:
ITEM: [item title]
GRADE: [numerical grade based on item's range]
EXPLANATION: [detailed explanation with specific evidence]
END_ITEM"""
        
        formatted_items = "\n\n".join(self.format_rubric_item(item) for item in items)
        
        # Create a repository structure summary
        repo_structure = {
            'documentation_files': list(content['documentation'].keys()),
            'code_files': list(content['code'].keys()),
            'data_files': content['data_metadata'],
            'other_files': list(content['other'].keys())
        }
        
        response = self.llm.invoke(prompt.format(
            items=formatted_items,
            repo_structure=json.dumps(repo_structure, indent=2)
        ))
        
        return self.parse_batch_response(response.content)

    def parse_batch_response(self, response: str) -> Dict[str, Any]:
        """Parse the LLM's grading response with improved multi-line handling"""
        grades = {}
        explanations = {}
        
        # Split response into item blocks
        items = response.split('ITEM:')
        
        for item_block in items[1:]:  # Skip first empty split
            lines = item_block.split('\n')
            current_item = lines[0].strip()
            current_grade = None
            explanation_lines = []
            
            in_explanation = False
            
            for line in lines[1:]:
                line = line.strip()
                if not line:
                    continue
                    
                if line.startswith('GRADE:'):
                    try:
                        current_grade = float(line.replace('GRADE:', '').strip())
                    except ValueError:
                        current_grade = 0
                elif line.startswith('EXPLANATION:'):
                    in_explanation = True
                    explanation_lines.append(line.replace('EXPLANATION:', '').strip())
                elif line == 'END_ITEM':
                    in_explanation = False
                elif in_explanation and not line.startswith('ITEM:'):
                    explanation_lines.append(line)
            
            if current_item and current_grade is not None:
                grades[current_item] = current_grade
                explanations[current_item] = ' '.join(explanation_lines)
        
        return {
            'grades': grades,
            'explanations': explanations
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