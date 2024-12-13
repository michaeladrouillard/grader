

const API_ENDPOINT = 'https://grader-a04u.onrender.com/api/grade'; // Replace with your deployed API endpoint

document.getElementById('gradeForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const repoUrl = document.getElementById('repoUrl').value;
    const submitBtn = document.getElementById('submitBtn');
    const loadingState = document.getElementById('loadingState');
    const results = document.getElementById('results');
    const resultsContent = document.getElementById('resultsContent');
    const error = document.getElementById('error');
    const progressUpdates = document.getElementById('progressUpdates');
    
    // Reset UI states
    submitBtn.disabled = true;
    loadingState.classList.remove('hidden');
    results.classList.add('hidden');
    error.classList.add('hidden');
    
    try {
        const response = await fetch(API_ENDPOINT, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ repoUrl }),
        });

        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || 'An error occurred while grading the repository');
        }

        // Display results
        resultsContent.innerHTML = formatResults(data.data);
        results.classList.remove('hidden');
    } catch (err) {
        error.querySelector('p').textContent = err.message;
        error.classList.remove('hidden');
    } finally {
        submitBtn.disabled = false;
        loadingState.classList.add('hidden');
    }
});

function formatResults(data) {
    const { grades, explanations, total_score } = data;
    
    let html = `
        <div class="mb-6">
            <h3 class="text-2xl font-bold text-blue-600">Overall Score: ${total_score.toFixed(2)}%</h3>
        </div>
    `;

    // Format critical items
    html += '<div class="mb-6"><h3 class="text-xl font-bold mb-4">Critical Items</h3>';
    Object.entries(grades)
        .filter(([title]) => data.critical_items?.includes(title))
        .forEach(([title, grade]) => {
            html += formatGradeItem(title, grade, explanations[title]);
        });
    html += '</div>';

    // Format regular items
    html += '<div><h3 class="text-xl font-bold mb-4">Regular Items</h3>';
    Object.entries(grades)
        .filter(([title]) => !data.critical_items?.includes(title))
        .forEach(([title, grade]) => {
            html += formatGradeItem(title, grade, explanations[title]);
        });
    html += '</div>';

    return html;
}

function formatGradeItem(title, grade, explanation) {
    return `
        <div class="border-b pb-4 mb-4">
            <h4 class="font-semibold">${title}</h4>
            <p class="text-gray-700 mb-2">Score: ${grade}</p>
            <p class="text-gray-600 text-sm">${explanation}</p>
        </div>
    `;
}