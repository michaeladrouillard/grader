// API endpoint
const API_URL = 'https://grader-a04u.onrender.com/api/grade';

// Define complete maxGrades object based on rubric
const maxGrades = {
    // Critical items (must pass these)
    'R/Python cited': 1,
    'Data cited': 1,
    'Class paper': 1,
    'LLM usage documented': 1,
    
    // Documentation items
    'Title': 2,
    'Author, date, and repo': 2,
    'Abstract': 4,
    'Introduction': 4,
    'Estimand': 1,
    
    // Core analysis items
    'Data': 10,
    'Measurement': 4,
    'Model': 10,
    'Results': 10,
    'Discussion': 10,
    
    // Quality items
    'Prose': 6,
    'Cross-references': 1,
    'Captions': 2,
    'Graphs and tables': 4,
    
    // Methodology items
    'Idealized methodology': 10,
    'Idealized survey': 4,
    'Pollster methodology overview and evaluation': 10,
    'Referencing': 4,
    
    // Technical items
    'Commits': 2,
    'Sketches': 2,
    'Simulation': 4,
    'Tests-simulation': 4,
    'Tests-actual': 4,
    'Parquet': 1,
    'Reproducible workflow': 4,
    'Miscellaneous': 3
};

// Define item categories for better organization
const itemCategories = {
    critical: [
        'R/Python cited',
        'Data cited',
        'Class paper',
        'LLM usage documented'
    ],
    documentation: [
        'Title',
        'Author, date, and repo',
        'Abstract',
        'Introduction',
        'Estimand'
    ],
    analysis: [
        'Data',
        'Measurement',
        'Model',
        'Results',
        'Discussion'
    ],
    quality: [
        'Prose',
        'Cross-references',
        'Captions',
        'Graphs and tables'
    ],
    methodology: [
        'Idealized methodology',
        'Idealized survey',
        'Pollster methodology overview and evaluation',
        'Referencing'
    ],
    technical: [
        'Commits',
        'Sketches',
        'Simulation',
        'Tests-simulation',
        'Tests-actual',
        'Parquet',
        'Reproducible workflow',
        'Miscellaneous'
    ]
};

document.getElementById('gradeForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const repoUrl = document.getElementById('repoUrl').value;
    const submitBtn = document.getElementById('submitBtn');
    const loadingState = document.getElementById('loadingState');
    const errorState = document.getElementById('errorState');
    const results = document.getElementById('results');
    const progress = document.getElementById('progress');
    
    // Reset states
    submitBtn.disabled = true;
    loadingState.classList.remove('hidden');
    errorState.classList.add('hidden');
    results.classList.add('hidden');
    progress.innerHTML = '';
    
    try {
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ repoUrl }),
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        if (!data.success) {
            throw new Error(data.error || 'An error occurred during grading');
        }

        displayResults(data.data);
        results.classList.remove('hidden');
    } catch (err) {
        document.getElementById('errorMessage').textContent = err.message;
        errorState.classList.remove('hidden');
    } finally {
        submitBtn.disabled = false;
        loadingState.classList.add('hidden');
    }
});

function displayResults(data) {
    const results = document.getElementById('results');
    results.innerHTML = ''; // Clear previous results

    // Create score summary card
    results.innerHTML = `
        <div class="bg-white p-6 rounded-lg shadow-lg mb-8">
            <h2 class="text-3xl font-bold text-gray-900">Overall Score: ${data.total_score.toFixed(2)}%</h2>
            ${data.timings ? `<p class="text-sm text-gray-500 mt-2">Graded in ${data.timings.total.toFixed(2)} seconds</p>` : ''}
        </div>
    `;

    // Helper function to create section
    function createSection(title, items, explanation = '') {
        const totalPoints = items.reduce((acc, item) => acc + (data.grades[item] || 0), 0);
        const maxPoints = items.reduce((acc, item) => acc + maxGrades[item], 0);
        
        return `
            <div class="bg-white p-6 rounded-lg shadow-lg mb-8">
                <div class="flex justify-between items-center mb-4">
                    <h2 class="text-2xl font-bold text-gray-900">${title}</h2>
                    <span class="text-lg font-semibold text-blue-600">${totalPoints}/${maxPoints} points</span>
                </div>
                ${explanation ? `<p class="text-gray-600 mb-4">${explanation}</p>` : ''}
                <div class="space-y-6">
                    ${items.map(item => createGradeItem(item, data.grades[item], data.explanations[item])).join('')}
                </div>
            </div>
        `;
    }

    // Helper function to create grade item
    function createGradeItem(title, grade, explanation) {
        const maxGrade = maxGrades[title];
        const scoreColor = grade === undefined ? 'text-gray-500' :
                          grade === 0 ? 'text-red-600' : 
                          grade === maxGrade ? 'text-green-600' : 'text-blue-600';
        
        const scoreText = grade === undefined ? 'Not graded' : `${grade}/${maxGrade}`;
        const scorePercentage = grade === undefined ? '-' : 
                               `(${((grade / maxGrade) * 100).toFixed(1)}%)`;
        
        return `
            <div class="border-t pt-4">
                <div class="flex justify-between items-start mb-2">
                    <h3 class="font-semibold text-lg text-gray-900">${title}</h3>
                    <div class="text-right">
                        <span class="${scoreColor} font-bold">${scoreText}</span>
                        <span class="text-gray-500 text-sm ml-2">${scorePercentage}</span>
                    </div>
                </div>
                <div class="prose prose-sm max-w-none text-gray-600">
                    ${marked.parse(explanation || 'Not evaluated')}
                </div>
            </div>
        `;
    }

    // Add sections in order
    results.innerHTML += createSection('Critical Requirements', itemCategories.critical, 
        'These items must pass for the paper to be accepted.');
    results.innerHTML += createSection('Documentation', itemCategories.documentation);
    results.innerHTML += createSection('Core Analysis', itemCategories.analysis);
    results.innerHTML += createSection('Quality', itemCategories.quality);
    results.innerHTML += createSection('Methodology', itemCategories.methodology);
    results.innerHTML += createSection('Technical Implementation', itemCategories.technical);

    // Add performance metrics if available
    if (data.timings) {
        results.innerHTML += `
            <div class="bg-white p-6 rounded-lg shadow-lg">
                <h2 class="text-2xl font-bold text-gray-900 mb-4">Performance Metrics</h2>
                <dl class="grid grid-cols-2 gap-4">
                    ${Object.entries(data.timings).map(([key, value]) => `
                        <div>
                            <dt class="text-sm font-medium text-gray-500">
                                ${key.replace(/_/g, ' ').toUpperCase()}
                            </dt>
                            <dd class="mt-1 text-sm text-gray-900">
                                ${value.toFixed(2)}s
                            </dd>
                        </div>
                    `).join('')}
                </dl>
            </div>
        `;
    }
}