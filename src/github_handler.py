import requests
from typing import Dict, List
import json

class GitHubRepo:
    def __init__(self, repo_url: str):
        self.repo_url = self._validate_github_url(repo_url)

    def _validate_github_url(self, url: str) -> str:
        """Validate and clean the GitHub URL."""
        if not url.startswith('https://github.com/'):
            raise ValueError("Invalid GitHub URL. Must start with 'https://github.com/'")
        return url.strip('/')

    def load_rubric(self) -> List[Dict]:
        """Load rubric items from JSON file."""
        with open('data/rubric.json', 'r') as f:
            return json.load(f)
        



import requests
from typing import Dict, List, Optional
import base64
import json
import os
from urllib.parse import urlparse

class GitHubRepo:
    def __init__(self, repo_url: str):
        self.repo_url = repo_url
        self.api_url = self._convert_to_api_url(repo_url)
        self.headers = {
            'Accept': 'application/vnd.github.v3+json'
        }
        if os.getenv('GITHUB_TOKEN'):
            self.headers['Authorization'] = f"token {os.getenv('GITHUB_TOKEN')}"
        
        # Cache the repo structure
        self.repo_structure = None
        print(f"Initialized GitHubRepo for: {repo_url}")

    def _convert_to_api_url(self, repo_url: str) -> str:
        """Convert GitHub web URL to API URL."""
        parsed = urlparse(repo_url)
        path_parts = parsed.path.strip('/').split('/')
        
        if len(path_parts) < 2:
            raise ValueError("Invalid GitHub URL")
        
        owner, repo = path_parts[0:2]
        api_url = f"https://api.github.com/repos/{owner}/{repo}"
        print(f"Converted URL to API URL: {api_url}")
        return api_url

    def get_repo_info(self) -> Dict:
        """Get basic repository information."""
        try:
            print("Fetching repository information...")
            response = requests.get(self.api_url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching repo info: {str(e)}")
            return {}

    def get_contents(self, path: str = "") -> List[Dict]:
        """Get contents of a directory or file in the repository."""
        try:
            url = f"{self.api_url}/contents/{path}"
            print(f"Fetching contents from: {url}")
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching contents: {str(e)}")
            return []

    def get_readme(self) -> str:
        """Get repository README content."""
        try:
            print("Fetching README...")
            url = f"{self.api_url}/readme"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            content = response.json()['content']
            return base64.b64decode(content).decode('utf-8')
        except requests.exceptions.RequestException as e:
            print(f"Error fetching README: {str(e)}")
            return ""

        def get_issues(self) -> List[Dict]:
        """Get repository issues."""
        try:
            print("Fetching issues...")
            url = f"{self.api_url}/issues"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching issues: {str(e)}")
            return []

    def get_file_content(self, path: str) -> str:
        """Get content of a specific file."""
        try:
            print(f"Fetching content for file: {path}")
            contents = self.get_contents(path)
            if isinstance(contents, list):
                print(f"Path {path} is a directory, not a file")
                return ""
            content = contents['content']
            return base64.b64decode(content).decode('utf-8')
        except Exception as e:
            print(f"Error fetching file content: {str(e)}")
            return ""

    def _recursive_get_contents(self, path: str = "") -> List[Dict]:
        """Recursively get contents of all directories."""
        print(f"Recursively fetching contents from: {path}")
        contents = []
        items = self.get_contents(path)
        
        for item in items:
            if item['type'] == 'dir':
                contents.extend(self._recursive_get_contents(item['path']))
            else:
                contents.append(item)
        
        return contents

    def get_repo_structure(self) -> Dict:
        """Get a complete structure of the repository including all important information."""
        if self.repo_structure is not None:
            return self.repo_structure

        print("Building complete repository structure...")
        try:
            self.repo_structure = {
                'basic_info': self.get_repo_info(),
                'readme': self.get_readme(),
                'issues': self.get_issues(),
                'files': self._recursive_get_contents(),
                'languages': self.get_languages(),
                'commits': self.get_recent_commits(),
                'rproj_files': self.find_files_by_extension('.Rproj'),
                'python_files': self.find_files_by_extension('.py'),
                'r_files': self.find_files_by_extension('.R'),
                'markdown_files': self.find_files_by_extension('.md')
            }
            print("Repository structure built successfully")
            return self.repo_structure
        except Exception as e:
            print(f"Error building repo structure: {str(e)}")
            return {}

    def get_languages(self) -> Dict:
        """Get languages used in the repository."""
        try:
            print("Fetching repository languages...")
            url = f"{self.api_url}/languages"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching languages: {str(e)}")
            return {}

        def get_recent_commits(self, count: int = 10) -> List[Dict]:
        """Get recent commits to the repository."""
        try:
            print(f"Fetching {count} most recent commits...")
            url = f"{self.api_url}/commits"
            params = {'per_page': count}
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching commits: {str(e)}")
            return []

    def find_files_by_extension(self, extension: str) -> List[Dict]:
        """Find all files with a specific extension in the repository."""
        print(f"Searching for files with extension: {extension}")
        all_files = self._recursive_get_contents()
        matching_files = [f for f in all_files if f['name'].lower().endswith(extension.lower())]
        print(f"Found {len(matching_files)} files with extension {extension}")
        return matching_files

    def check_file_exists(self, filename: str) -> bool:
        """Check if a file exists in the repository."""
        try:
            print(f"Checking if file exists: {filename}")
            self.get_contents(filename)
            print(f"File {filename} exists")
            return True
        except:
            print(f"File {filename} does not exist")
            return False

    def load_rubric(self) -> List[Dict]:
        """Load rubric from the JSON file."""
        print("Loading rubric from JSON file...")
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        rubric_path = os.path.join(project_root, 'data', 'rubric.json')
        
        try:
            with open(rubric_path, 'r') as f:
                rubric_data = json.load(f)
                print(f"Successfully loaded {len(rubric_data['rubric_items'])} rubric items")
                return rubric_data['rubric_items']
        except Exception as e:
            print(f"Error loading rubric: {str(e)}")
            return []

    def get_repository_analysis(self) -> Dict:
        """
        Perform a comprehensive analysis of the repository.
        Returns a dictionary with various metrics and information useful for assessment.
        """
        print("Performing comprehensive repository analysis...")
        try:
            repo_structure = self.get_repo_structure()
            
            analysis = {
                'has_readme': bool(repo_structure['readme']),
                'readme_length': len(repo_structure['readme']),
                'total_files': len(repo_structure['files']),
                'languages_used': list(repo_structure['languages'].keys()),
                'has_rproj': bool(repo_structure['rproj_files']),
                'has_python': bool(repo_structure['python_files']),
                'has_r': bool(repo_structure['r_files']),
                'has_markdown': bool(repo_structure['markdown_files']),
                'total_commits': len(repo_structure['commits']),
                'open_issues': len(repo_structure['issues']),
                'file_structure': self._analyze_file_structure(),
                'readme_analysis': self._analyze_readme(repo_structure['readme']),
                'citation_analysis': self._analyze_citations(),
                'class_project_indicators': self._check_class_project_indicators()
            }
            
            print("Repository analysis completed successfully")
            return analysis
            
        except Exception as e:
            print(f"Error during repository analysis: {str(e)}")
            return {}

    def _analyze_file_structure(self) -> Dict:
        """Analyze the repository's file structure."""
        print("Analyzing file structure...")
        try:
            all_files = self._recursive_get_contents()
            return {
                'total_directories': len(set(os.path.dirname(f['path']) for f in all_files)),
                'file_types': self._count_file_types(all_files),
                'has_data_directory': any(f['path'].lower().startswith('data/') for f in all_files),
                'has_src_directory': any(f['path'].lower().startswith('src/') for f in all_files),
                'has_tests_directory': any(f['path'].lower().startswith('tests/') for f in all_files)
            }
        except Exception as e:
            print(f"Error analyzing file structure: {str(e)}")
            return {}

    def _count_file_types(self, files: List[Dict]) -> Dict:
        """Count the number of files by extension."""
        print("Counting file types...")
        extensions = {}
        for file in files:
            _, ext = os.path.splitext(file['name'])
            if ext:
                extensions[ext.lower()] = extensions.get(ext.lower(), 0) + 1
        return extensions

    def _analyze_readme(self, readme_content: str) -> Dict:
        """Analyze the README content for key components."""
        print("Analyzing README content...")
        return {
            'has_title': bool(readme_content.split('\n')[0].strip()),
            'has_description': len(readme_content) > 100,
            'has_installation_section': 'installation' in readme_content.lower(),
            'has_usage_section': 'usage' in readme_content.lower(),
            'has_llm_usage_section': any(term in readme_content.lower() 
                                       for term in ['llm', 'chatgpt', 'gpt', 'large language model', 'copilot']),
            'mentions_data_sources': any(term in readme_content.lower() 
                                       for term in ['data source', 'dataset', 'data from']),
            'has_references': any(term in readme_content.lower() 
                                for term in ['reference', 'citation', 'cited', 'bibliography']),
            'word_count': len(readme_content.split()),
            'has_code_blocks': '```' in readme_content,
            'has_links': '[' in readme_content and '](' in readme_content
        }

    def _analyze_citations(self) -> Dict:
        """Analyze repository for proper citations."""
        print("Analyzing citations...")
        files_to_check = ['README.md', 'REFERENCES.md', 'references.md', 'bibliography.md']
        citations_found = []
        
        for file in files_to_check:
            content = self.get_file_content(file)
            if content:
                # Look for common citation patterns
                citations_found.extend(self._extract_citations(content))

        return {
            'has_citations': bool(citations_found),
            'citation_count': len(citations_found),
            'has_r_citation': any('r-project' in cite.lower() or 'r core team' in cite.lower() 
                                for cite in citations_found),
            'has_python_citation': any('python' in cite.lower() for cite in citations_found),
            'citations_found': citations_found
        }

    def _extract_citations(self, content: str) -> List[str]:
        """Extract citations from content using common patterns."""
        citations = []
        citation_patterns = [
            r'\[(.*?)\]',  # [Author, Year]
            r'\((.*?)\)',  # (Author, Year)
            r'@\w+\{.*?\}',  # BibTeX entries
            r'doi:[\S]+',  # DOI references
            r'https://doi\.org/\S+',  # DOI URLs
            r'(?<=[^A-Za-z])(R Core Team|Python Software Foundation)',  # Direct mentions
            r'(?<=cite{)(.*?)(?=})'  # LaTeX citations
        ]
        
        for pattern in citation_patterns:
            import re
            matches = re.findall(pattern, content)
            citations.extend(matches)
        
        return list(set(citations))  # Remove duplicates

    def _check_class_project_indicators(self) -> Dict:
        """Check for indicators that this is a class project."""
        print("Checking for class project indicators...")
        indicators = {
            'filename_indicators': False,
            'readme_indicators': False,
            'comment_indicators': False,
            'rproj_indicators': False
        }
        
        # Check filenames and paths
        all_files = self._recursive_get_contents()
        class_related_terms = ['assignment', 'homework', 'class', 'course', 'project', 
                             'exercise', 'tutorial', 'workshop', 'student']
        
        # Check file and directory names
        for file in all_files:
            if any(term in file['path'].lower() for term in class_related_terms):
                indicators['filename_indicators'] = True
                break

        # Check README content
        readme = self.get_readme().lower()
        if any(term in readme for term in class_related_terms):
            indicators['readme_indicators'] = True

        # Check R and Python files for comments
        for ext in ['.R', '.py']:
            files = self.find_files_by_extension(ext)
            for file in files:
                content = self.get_file_content(file['path']).lower()
                if any(term in content for term in class_related_terms):
        