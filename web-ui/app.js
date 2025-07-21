// Smart File Manager Web UI JavaScript

const API_BASE_URL = 'http://localhost:8001';

// Load statistics on page load
document.addEventListener('DOMContentLoaded', () => {
    loadStatistics();
    loadDiskUsage();
    
    // Set up search form handler
    const searchForm = document.getElementById('search-form');
    searchForm.addEventListener('submit', handleSearch);
});

// Load system statistics
async function loadStatistics() {
    try {
        const response = await fetch(`${API_BASE_URL}/stats/multimedia`);
        const data = await response.json();
        
        if (data.indexer_statistics) {
            document.getElementById('total-files').textContent = 
                data.indexer_statistics.total_files?.toLocaleString() || '0';
            
            const multimediaCount = data.indexer_statistics.by_media_type?.multimedia?.count || 0;
            document.getElementById('multimedia-files').textContent = 
                multimediaCount.toLocaleString();
            
            // Count AI analyzed files
            let aiAnalyzed = 0;
            if (data.indexer_statistics.content_extraction) {
                aiAnalyzed = data.indexer_statistics.content_extraction.ai_analyzed || 0;
            }
            document.getElementById('ai-analyzed').textContent = aiAnalyzed.toLocaleString();
        }
    } catch (error) {
        console.error('Failed to load statistics:', error);
        document.getElementById('total-files').textContent = 'Error';
        document.getElementById('multimedia-files').textContent = 'Error';
        document.getElementById('ai-analyzed').textContent = 'Error';
    }
}

// Load disk usage
async function loadDiskUsage() {
    try {
        const response = await fetch(`${API_BASE_URL}/disk/usage`);
        const data = await response.json();
        
        if (data.success && data.data) {
            const usage = data.data.usage_percent;
            const element = document.getElementById('disk-usage');
            element.textContent = `${usage.toFixed(1)}%`;
            
            // Add color coding based on usage
            if (usage >= 90) {
                element.style.color = '#e74c3c';
            } else if (usage >= 80) {
                element.style.color = '#f39c12';
            } else {
                element.style.color = '#27ae60';
            }
        }
    } catch (error) {
        console.error('Failed to load disk usage:', error);
        document.getElementById('disk-usage').textContent = 'Error';
    }
}

// Handle search form submission
async function handleSearch(event) {
    event.preventDefault();
    
    const query = document.getElementById('search-query').value;
    const mediaType = document.getElementById('media-type').value;
    const resultsContainer = document.getElementById('results-container');
    
    // Show loading state
    resultsContainer.innerHTML = '<div class="loading">Searching...</div>';
    
    try {
        const requestBody = {
            query: query,
            limit: 20
        };
        
        if (mediaType) {
            requestBody.media_types = [mediaType];
        }
        
        const response = await fetch(`${API_BASE_URL}/search/multimedia`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });
        
        const data = await response.json();
        
        if (data.success && data.results) {
            displayResults(data.results);
        } else {
            resultsContainer.innerHTML = '<div class="error">Search failed. Please try again.</div>';
        }
    } catch (error) {
        console.error('Search failed:', error);
        resultsContainer.innerHTML = '<div class="error">Search error: ' + error.message + '</div>';
    }
}

// Display search results
function displayResults(results) {
    const resultsContainer = document.getElementById('results-container');
    
    if (results.length === 0) {
        resultsContainer.innerHTML = '<div class="loading">No results found.</div>';
        return;
    }
    
    const html = results.map(file => {
        const sizeInMB = (file.size / 1024 / 1024).toFixed(2);
        const score = (file.score * 100).toFixed(1);
        const modifiedDate = new Date(file.modified_time * 1000).toLocaleDateString();
        
        return `
            <div class="result-item">
                <h3>${file.highlighted_name || file.name}</h3>
                <div class="path">${file.path}</div>
                <div class="meta">
                    <span>📁 ${file.media_type} / ${file.category}</span>
                    <span>💾 ${sizeInMB} MB</span>
                    <span>📅 ${modifiedDate}</span>
                    <span class="score">⭐ ${score}% match</span>
                </div>
            </div>
        `;
    }).join('');
    
    resultsContainer.innerHTML = html;
}

// Auto-refresh statistics every 30 seconds
setInterval(() => {
    loadStatistics();
    loadDiskUsage();
}, 30000);