
    const API_URL = 'https://grader-a04u.onrender.com/api/grade';

    // Define complete maxGrades object based on rubric
    const maxGrades = {
        // Critical items
        'R/Python cited': 1,
        'Data cited': 1,
        'Class paper': 1,
        'LLM usage documented': 1,
        
        // Standard items
        'Title': 2,
        'Author, date, and repo': 2,
        'Abstract': 4,
        'Introduction': 4,
        'Estimand': 1,
        'Data': 10,
        'Measurement': 4,
        'Model': 10,
        'Results': 10,
        'Discussion': 10,
        'Prose': 6,
        'Cross-references': 1,
        'Captions': 2,
        'Graphs and tables': 4,
        'Idealized methodology': 10,
        'Idealized survey': 4,
        'Pollster methodology overview and evaluation': 10,
        'Referencing': 4,
        'Commits': 2,
        'Sketches': 2,
        'Simulation': 4,
        'Tests-simulation': 4,
        'Tests-actual': 4,
        'Parquet': 1,
        'Reproducible workflow': 4,
        'Miscellaneous': 3
    };

    // Define critical items list
    const criticalItems = [
        'R/Python cited',
        'Data cited',
        'Class paper',
        'LLM usage documented'
    ];

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
        // Update total score
        document.getElementById('totalScore').textContent = `${data.total_score.toFixed(2)}%`;

        // Clear previous results
        const criticalList = document.getElementById('criticalItemsList');
        const regularList = document.getElementById('regularItemsList');
        criticalList.innerHTML = '';
        regularList.innerHTML = '';

        // Helper function to create grade item HTML with better formatting
        const createGradeItem = (title, grade, explanation) => {
            const maxGrade = maxGrades[title];
            const scoreColor = grade === 0 ? 'text-red-600' : 
                             grade === maxGrade ? 'text-green-600' : 'text-blue-600';
            const scorePercentage = ((grade / maxGrade) * 100).toFixed(1);
            
            return `
                <div class="bg-white p-6 rounded-lg shadow-md mb-4">
                    <div class="flex justify-between items-start mb-3">
                        <h3 class="font-semibold text-lg text-gray-900">${title}</h3>
                        <div class="text-right">
                            <span class="${scoreColor} font-bold">${grade}/${maxGrade}</span>
                            <span class="text-gray-500 text-sm ml-2">(${scorePercentage}%)</span>
                        </div>
                    </div>
                    <div class="prose prose-sm max-w-none text-gray-600">
                        ${marked.parse(explanation || 'No explanation provided')}
                    </div>
                </div>
            `;
        };

        // Sort items by title for consistent display
        const sortedEntries = Object.entries(data.grades).sort((a, b) => a[0].localeCompare(b[0]));

        // Process all items
        sortedEntries.forEach(([title, grade]) => {
            const explanation = data.explanations[title];
            const isCritical = criticalItems.includes(title);
            const gradeHtml = createGradeItem(title, grade, explanation);
            
            if (isCritical) {
                criticalList.innerHTML += gradeHtml;
            } else {
                regularList.innerHTML += gradeHtml;
            }
        });

        // Show timings if available
        if (data.timings) {
            const timingsHtml = `
                <div class="mt-8 bg-gray-50 p-6 rounded-lg">
                    <h3 class="text-lg font-semibold mb-3">Performance Metrics</h3>
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
            document.getElementById('results').insertAdjacentHTML('beforeend', timingsHtml);
        }
    }

    function updateProgress(message) {
        const progress = document.getElementById('progress');
        const timestamp = new Date().toLocaleTimeString();
        progress.innerHTML += `<div>${timestamp}: ${message}</div>`;
        progress.scrollTop = progress.scrollHeight;
    }
