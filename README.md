# grader



this is an app where rohan's students can submit their ongoing projects and get tailored feedback from an LLM according to his [rubric](https://tellingstorieswithdata.com/25-papers.html#rubric-5).
it uses the github API and Claude opus to crawl and evaluate repository content (markdown files, code, repo structure, etc) and provide detailed feedback.


i used Claude for a lot of the debugging in this project and also for navigating previously uncharted waters of javascript/flask/render


## Table of Contents
- [Prerequisites](#prerequisites)
- [Setup Instructions](#setup-instructions)
  - [Step 1: Local Setup](#step-1-local-setup)
  - [Step 2: API Keys](#step-2-api-keys)
  - [Step 3: Local Configuration](#step-3-local-configuration)
  - [Step 4: Deployment to Render](#step-4-deployment-to-render)
  - [Step 5: Frontend Setup](#step-5-frontend-setup)
- [Costs](#costs)
- [Customizing for a Different Rubric](#customizing-for-a-different-rubric)
  - [Updating the Rubric](#updating-the-rubric)
  - [Update Frontend Configuration](#update-frontend-configuration)
  - [Update Backend Processing](#update-backend-processing)
  - [Potential Pitfalls](#potential-pitfalls)
- [Contributing](#contributing)





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


## Customizing for a Different Rubric

### Updating the Rubric

Use an LLM for all of this it will go much faster lol.

1. **Modify rubric.json**
   - Locate `src/data/rubric.json`
   - Follow this structure for each rubric item:
   ```json
   {
     "rubric_items": [
       {
         "title": "Item Name",
         "range": {
           "min": 0,
           "max": 10  // Maximum possible points
         },
         "values": {
           "0": "Poor or not done",
           "2": "Some issues",
           "4": "Acceptable",
           "6": "Exceeds expectations",
           "8": "Exceptional"
         },
         "criteria": "Detailed description of what to look for when grading this item",
         "critical": false  // Set to true if failing this item should result in zero overall
       }
     ]
   }
   ```
   
2. **Important Notes About Rubric Structure**:
   - Each item MUST have a UNIQUE `title`
   - The `values` object must include all possible scores
   - Scores must be within the `range.min` and `range.max`
   - `critical` items should use a max score of 1 (pass/fail). This is for items where if the student doesnt do it, they fail the assignment entirely.

### Update Frontend Configuration

1. Modify `maxGrades` in `docs/js/grader.js`:
```javascript
const maxGrades = {
    'Your Item Name': maximum_points,
    // Add all your rubric items here
};
```

2. Update item categories:
```javascript
const itemCategories = {
    critical: [
        // Your critical items
    ],
    documentation: [
        // Your documentation items
    ],
    // Add other categories as needed
};
```

### Update Backend Processing

Modify category assignments in `src/repo_grader.py`:
```python
# In batch_grade_rubric method
doc_items = [item for item in self.rubric 
            if not item.get('critical', False) and 
            item['title'].lower() in ['your', 'document', 'items']]

tech_items = [item for item in self.rubric 
             if not item.get('critical', False) and 
             item['title'].lower() in ['your', 'technical', 'items']]
```

The backend works this way to drastically reduce the amount of tokens/LLM calls needed to grade a repo by grouping rubric items into batches based on which docs the LLM should look at.
So, the tech items will look at .py, .ipynb, etc files and so on. 
Depending on your rubric, you may have to play around with this, but this is basically the main juncture where you can reduce costs/latency.

Once you set this up, [test locally](#step-3-local-configuration).


### Potential pitfalls

- Inconsistent item names between rubric and code
- Forgetting to update both frontend and backend
- Not properly setting up the [backend processing](#update-backend-processing) (i.e., during a test run the LLM wasn't grading a rubric item that evaluated whether the student put their name and date. this information would have been found in the docs (.qmd, .pdf, etc.) but instead this item ended up in a batch that was fed repo structure and metadata)


## Contributing

Feel free to submit issues and pull requests for any improvements :-) I only tested this for the election forecasting assignment, so there may be hiccups for other kinds of rubrics.
