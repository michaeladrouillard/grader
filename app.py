from flask import Flask, request, jsonify
from flask_cors import CORS
from src.repo_grader import RepoGrader
from src.config import GITHUB_API_TOKEN, ANTHROPIC_API_TOKEN

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/api/grade', methods=['POST'])
def grade_repo():
    try:
        data = request.get_json()
        repo_url = data.get('repoUrl')
        
        if not repo_url:
            return jsonify({'error': 'Repository URL is required'}), 400

        # Parse GitHub URL
        parts = repo_url.strip("/").split("/")
        owner = parts[-2]
        repo = parts[-1]

        # Initialize grader
        grader = RepoGrader(
            github_token=GITHUB_API_TOKEN,
            anthropic_api_key=ANTHROPIC_API_TOKEN,
            rubric_path="src/data/rubric.json"
        )

        # Grade repository
        results = grader.analyze_repo(owner, repo)
        
        return jsonify({
            'success': True,
            'data': results
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True)