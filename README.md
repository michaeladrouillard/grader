# grader



this is an app where rohan's students can submit their ongoing projects and get tailored feedback from an LLM according to his [rubric](https://tellingstorieswithdata.com/25-papers.html#rubric-5).
it uses Claude opus to evaluate repository content (markdown files, code, repo structure, etc) and provide detailed feedback

i used Claude for a lot of the debugging in this project and also for navigating previously uncharted waters of javascript/flask/render

## Setup Instructions

### Prerequisites
- [Anthropic account](https://www.anthropic.com/) for Claude API access
- [Render account](https://render.com/) for deployment

### Step 1: Local Setup

1. Clone the repository:
```bash
git clone https://github.com/michaeladrouillard/grader.git
cd grader
```

2. Create a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # on Windows, use: venv\Scripts\activate
pip install -r requirements.txt
```

### Step 2: API Keys

1. **GitHub API Key**:
   - GitHub Settings > Developer settings > Personal access tokens > Tokens (classic)
   - Generate new token with `repo` scope

2. **Anthropic API Key**:
   - Go to [Console](https://console.anthropic.com/)
   - Generate an API key

### Step 3: Local Configuration

1. Create a `config.py` file in the `src` directory:
```python
GITHUB_API_TOKEN = 'your_github_token_here'
ANTHROPIC_API_KEY = 'your_anthropic_key_here'
```
You can also use os so you don't have to hardcode it or whatever here. But just make sure you .gitignore this file

2. Test locally:
```bash
python src/repo_grader.py https://github.com/username/repositoryThatYouWantToEvaluateUsingThisApp
```

### Step 4: Deployment to Render

1. Create a new Web Service on Render:
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Click "New +" and select "Web Service"
   - Connect your GitHub repository

2. Configure the Web Service:
   - Name: Choose a name (e.g., "paper-grader")
   - Environment: Python 3
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python app.py`
   - Add Environment Variables:
     - `GITHUB_API_TOKEN`: Your GitHub token
     - `ANTHROPIC_API_KEY`: Your Anthropic API key

3. Deploy your service:
   - Click "Create Web Service"
   - Wait for deployment to complete

### Step 5: Frontend Setup

1. Update the API endpoint in `docs/js/grader.js`:
```javascript
const API_URL = 'https://your-render-service-name.onrender.com/api/grade';
```

2. Deploy the frontend to GitHub Pages:
   - Go to repository Settings > Pages
   - Set source to GitHub Actions
   - Commit and push your changes
   - Wait for the GitHub Action to complete

The grader should now be accessible at `https://yourusername.github.io/grader`!


## Costs

The app uses Claude 3 Opus, and when I tested it on repos students submitted for the election forecasting assignment it came out to about $0.70 per run.
YMMV based on the repo/prompt/token count being ingested by the model, and you can track cost stuff on the [Anthropic Console](https://console.anthropic.com/).

## Contributing

Feel free to submit issues and pull requests for any improvements :-) I only tested this for the election forecasting assignment, so there may be hiccups for other kinds of rubrics.
