const urlParams = new URLSearchParams(window.location.search);
const sessionId = urlParams.get('session');

let sessionMaxMarks = 100;
let sessionClassSize = 60;

// Fix #5: WebSocket reconnection with exponential backoff
let wsReconnectDelay = 1000; // Start at 1 second
const WS_MAX_RECONNECT_DELAY = 30000; // Cap at 30 seconds

// Chart.js Setup
Chart.defaults.color = '#a0a5ba';
Chart.defaults.font.family = "'Inter', sans-serif";

const ctx = document.getElementById('histogramChart').getContext('2d');
let histogramChart = new Chart(ctx, {
    type: 'bar',
    data: {
        labels: [],
        datasets: [{
            label: 'Number of Students',
            data: [],
            backgroundColor: 'rgba(109, 40, 217, 0.7)',
            borderColor: 'rgba(109, 40, 217, 1)',
            borderWidth: 1,
            borderRadius: 6,
            barPercentage: 0.8
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            y: {
                beginAtZero: true,
                ticks: { stepSize: 1 },
                grid: { color: 'rgba(255, 255, 255, 0.05)' }
            },
            x: {
                grid: { display: false }
            }
        },
        plugins: {
            legend: { display: false }
        }
    }
});

function initDashboard() {
    if (!sessionId) {
        document.getElementById('examTitle').textContent = "Invalid Session Link";
        return;
    }
    
    // Fetch Session info
    fetch(`/api/sessions/${sessionId}`)
        .then(res => res.json())
        .then(data => {
            document.getElementById('examTitle').textContent = data.name;
            sessionMaxMarks = data.max_marks;
            sessionClassSize = data.class_size;
            
            // Connect WebSocket immediately after getting session context
            connectWebSocket();
            
            // Fetch initial stats
            fetchStats();
        })
        .catch(err => {
            console.error("Error fetching session config", err);
            document.getElementById('examTitle').textContent = "Connection Error or Expired Session";
        });
}

function fetchStats() {
    fetch(`/api/sessions/${sessionId}/dashboard`)
        .then(res => res.json())
        .then(updateUI)
        .catch(console.error);
}

function connectWebSocket() {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${window.location.host}/api/sessions/${sessionId}/ws`;
    const ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
        // Fix #5: Reset backoff delay on successful connection
        wsReconnectDelay = 1000;
    };

    ws.onmessage = (event) => {
        const statsData = JSON.parse(event.data);
        updateUI(statsData);
    };
    
    ws.onclose = () => {
        // Fix #5: Exponential backoff with jitter to prevent thundering herd
        const jitter = Math.random() * 1000; // 0-1s random jitter
        const delay = Math.min(wsReconnectDelay + jitter, WS_MAX_RECONNECT_DELAY);
        console.log(`WebSocket disconnected. Reconnecting in ${Math.round(delay / 1000)}s...`);
        setTimeout(connectWebSocket, delay);
        // Double the delay for next attempt (exponential backoff)
        wsReconnectDelay = Math.min(wsReconnectDelay * 2, WS_MAX_RECONNECT_DELAY);
    };
}

function updateUI(data) {
    if (data.count === 0) {
        document.getElementById('countDisplay').textContent = `0/${sessionClassSize}`;
        return;
    }

    document.getElementById('countDisplay').textContent = `${data.count}/${sessionClassSize}`;
    
    document.getElementById('statMean').textContent = data.mean !== null ? data.mean : "-";
    document.getElementById('statMedian').textContent = data.median !== null ? data.median : "-";
    document.getElementById('statMode').textContent = data.mode !== null ? data.mode : "-";
    document.getElementById('statStdDev').textContent = data.std_dev !== null ? data.std_dev : "-";
    document.getElementById('statMin').textContent = data.min !== null ? data.min : "-";
    document.getElementById('statMax').textContent = data.max !== null ? data.max : "-";
    
    document.getElementById('statQ1').textContent = data.q1 !== null ? data.q1 : "-";
    document.getElementById('statQ2').textContent = data.median !== null ? data.median : "-";
    document.getElementById('statQ3').textContent = data.q3 !== null ? data.q3 : "-";

    document.getElementById('interpretationText').textContent = data.interpretation || "Parsing data...";

    // Update Progress Bars for Quartiles
    if (data.q1 !== null) {
        document.getElementById('barQ1').style.width = `${(data.q1 / sessionMaxMarks) * 100}%`;
        document.getElementById('barQ2').style.width = `${(data.median / sessionMaxMarks) * 100}%`;
        document.getElementById('barQ3').style.width = `${(data.q3 / sessionMaxMarks) * 100}%`;
    }

    // Update Chart
    if (data.histogram_json) {
        const histData = JSON.parse(data.histogram_json);
        histogramChart.data.labels = histData.labels;
        histogramChart.data.datasets[0].data = histData.data;
        histogramChart.update();
    }

    // Render Bell Curve if applicable
    if (sessionMaxMarks === 100 && data.std_dev > 0 && data.count > 0 && data.raw_scores_json) {
        document.getElementById('relative-grading-container').classList.remove('d-none');
        
        const mu = parseFloat(data.mean);
        const sigma = parseFloat(data.std_dev);
        const rawScores = JSON.parse(data.raw_scores_json);
        
        // Boundaries
        const boundS = mu + 1.5 * sigma;
        const boundA = mu + 0.5 * sigma;
        const boundB = mu - 0.5 * sigma;
        const boundC = mu - 1.0 * sigma;
        const boundD = mu - 1.5 * sigma;
        const rawBoundE = mu - 2.0 * sigma;
        
        const boundE = Math.max(40, rawBoundE); // floor E at 40
        const boundF = 40; // Hard fail threshold
        
        // Update table
        const tbody = document.getElementById('grade-table-body');
        tbody.innerHTML = '';
        
        const addRow = (grade, range, color) => {
            tbody.innerHTML += `<tr>
                <td style="padding: 0.5rem; color: ${color}; font-weight: bold;">${grade}</td>
                <td style="padding: 0.5rem;">${range}</td>
            </tr>`;
        };
        
        if (boundS <= 100) {
            addRow('S (Outstanding)', `&ge; ${boundS.toFixed(2)}`, '#8b5cf6'); // purple
        }
        addRow('A (Excellent)', `${boundA.toFixed(2)} - ${boundS > 100 ? '100.00' : (boundS - 0.01).toFixed(2)}`, '#3b82f6'); // blue
        addRow('B (Very Good)', `${boundB.toFixed(2)} - ${(boundA - 0.01).toFixed(2)}`, '#10b981'); // green
        addRow('C (Good)', `${boundC.toFixed(2)} - ${(boundB - 0.01).toFixed(2)}`, '#f59e0b'); // yellow
        addRow('D (Average)', `${boundD.toFixed(2)} - ${(boundC - 0.01).toFixed(2)}`, '#f97316'); // orange
        if (boundD > 40) {
            addRow('E (Pass)', `40.00 - ${(boundD - 0.01).toFixed(2)}`, '#ec4899'); // pink
        }
        addRow('F (Fail)', `< 40.00`, '#ef4444'); // red
        
        // Generator for PDF
        const pdf = (x) => (1 / (sigma * Math.sqrt(2 * Math.PI))) * Math.exp(-0.5 * Math.pow((x - mu) / sigma, 2));
        
        // To build datasets for shading, we create fine data points
        const createDataset = (minX, maxX, grade, color) => {
            const points = [];
            for (let x = minX; x <= maxX; x += 0.5) {
                if (x >= 0 && x <= 100) points.push({ x: x, y: pdf(x) });
            }
            if (maxX >= 0 && maxX <= 100) points.push({ x: maxX, y: pdf(maxX) }); // Ensure end boundary
            return {
                label: grade,
                data: points,
                borderColor: color,
                backgroundColor: color + '40', // transparent fill
                fill: 'origin',
                pointRadius: 0,
                borderWidth: 2
            };
        };
        
        const datasets = [];
        datasets.push(createDataset(0, boundF, 'F', '#ef4444'));
        if (boundD > 40) {
            datasets.push(createDataset(boundF, boundD, 'E', '#ec4899'));
        }
        datasets.push(createDataset(Math.max(boundD, boundF), boundC, 'D', '#f97316'));
        datasets.push(createDataset(boundC, boundB, 'C', '#f59e0b'));
        datasets.push(createDataset(boundB, boundA, 'B', '#10b981'));
        datasets.push(createDataset(boundA, Math.min(boundS, 100), 'A', '#3b82f6'));
        if (boundS <= 100) {
            datasets.push(createDataset(boundS, 100, 'S', '#8b5cf6'));
        }
        
        // Scatter points
        const scatterData = rawScores.map(score => ({ x: score, y: pdf(score) }));
        datasets.push({
            type: 'scatter',
            label: 'Students',
            data: scatterData,
            backgroundColor: '#ffffff',
            borderColor: '#a0a5ba',
            borderWidth: 1,
            pointRadius: 5,
            pointHoverRadius: 5
        });
        
        if (!window.bellCurveChart) {
            const bellCtx = document.getElementById('bellCurveChart');
            window.bellCurveChart = new Chart(bellCtx, {
                type: 'line',
                data: { datasets: datasets },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: { type: 'linear', min: 0, max: 100, ticks: { color: '#a0a5ba' } },
                        y: { display: false }
                    },
                    plugins: {
                        legend: { display: false },
                        tooltip: { enabled: false }
                    }
                }
            });
        } else {
            window.bellCurveChart.data.datasets = datasets;
            window.bellCurveChart.update();
        }
        
    } else {
        const c = document.getElementById('relative-grading-container');
        if (c) c.classList.add('d-none');
    }
}

initDashboard();
