const urlParams = new URLSearchParams(window.location.search);
const sessionId = urlParams.get('session');

let sessionMaxMarks = 100;
let sessionClassSize = 60;

// WebSocket reconnection with exponential backoff
let wsReconnectDelay = 1000;
const WS_MAX_RECONNECT_DELAY = 30000;

// Chart.js global defaults
Chart.defaults.color = '#a0a5ba';
Chart.defaults.font.family = "'Inter', sans-serif";
Chart.defaults.plugins.tooltip.backgroundColor = '#191b26';
Chart.defaults.plugins.tooltip.borderColor = 'rgba(255,255,255,0.1)';
Chart.defaults.plugins.tooltip.borderWidth = 1;
Chart.defaults.plugins.tooltip.padding = 10;

let histogramChart, quartilesChart, bellCurveChart;

function initCharts() {
    // ── Histogram (Score Distribution) ──
    const ctxHist = document.getElementById('histogramChart').getContext('2d');
    histogramChart = new Chart(ctxHist, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                label: 'Students',
                data: [],
                backgroundColor: 'rgba(109, 40, 217, 0.5)',
                borderColor: '#6d28d9',
                borderWidth: 1,
                borderRadius: 4,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { grid: { display: false } },
                y: {
                    beginAtZero: true,
                    ticks: { stepSize: 1 },
                    grid: { color: 'rgba(255,255,255,0.05)' }
                }
            }
        }
    });

    // ── Quartiles (horizontal bars) ──
    const ctxQ = document.getElementById('quartilesChart').getContext('2d');
    quartilesChart = new Chart(ctxQ, {
        type: 'bar',
        data: {
            labels: ['Q3 (75th Percentile)', 'Q2 (Median)', 'Q1 (25th Percentile)'],
            datasets: [{
                data: [0, 0, 0],
                backgroundColor: ['#6d28d9', '#f59e0b', '#ef4444'],
                borderRadius: 4,
                barPercentage: 0.6
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: (ctx) => `${ctx.parsed.x}`
                    }
                }
            },
            scales: {
                x: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.05)' } },
                y: { grid: { display: false } }
            }
        }
    });
}

function initDashboard() {
    if (!sessionId) {
        document.getElementById('examTitle').textContent = "Invalid Session Link";
        return;
    }

    initCharts();

    fetch(`/api/sessions/${sessionId}`)
        .then(res => res.json())
        .then(data => {
            document.getElementById('examTitle').textContent = data.name;
            sessionMaxMarks = data.max_marks;
            sessionClassSize = data.class_size;
            window.sessionNameStr = data.name;

            connectWebSocket();
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

    ws.onopen = () => wsReconnectDelay = 1000;
    ws.onmessage = (event) => updateUI(JSON.parse(event.data));
    ws.onclose = () => {
        const jitter = Math.random() * 1000;
        const delay = Math.min(wsReconnectDelay + jitter, WS_MAX_RECONNECT_DELAY);
        setTimeout(connectWebSocket, delay);
        wsReconnectDelay = Math.min(wsReconnectDelay * 2, WS_MAX_RECONNECT_DELAY);
    };
}

function updateUI(data) {
    if (data.count === 0) {
        document.getElementById('countDisplay').textContent = `0/${sessionClassSize}`;
        return;
    }

    document.getElementById('countDisplay').textContent = `${data.count}/${sessionClassSize}`;
    document.getElementById('interpretationText').textContent = data.interpretation || "Sufficient data required for AI interpretation.";

    // ── Stat Cards ──
    document.getElementById('statMean').textContent = data.mean !== null ? data.mean.toFixed(1) : "-";
    document.getElementById('statMedian').textContent = data.median !== null ? data.median.toFixed(1) : "-";
    document.getElementById('statMode').textContent = data.mode !== null ? data.mode.toFixed(1) : "-";

    const isOverallMarks = window.sessionNameStr && window.sessionNameStr.includes('Overall Marks');
    document.getElementById('statStdDev').textContent = (data.std_dev !== null && isOverallMarks) ? data.std_dev.toFixed(3) : "-";

    document.getElementById('statLowest').textContent = data.min !== null ? data.min : "-";
    document.getElementById('statHighest').textContent = data.max !== null ? data.max : "-";

    const rawScores = data.raw_scores_json ? JSON.parse(data.raw_scores_json) : [];

    // ── Raw Scores Tape ──
    const scoreBucket = document.getElementById('raw-scores-bucket');
    if (scoreBucket) {
        if (rawScores.length === 0) {
            scoreBucket.innerHTML = '<span style="color: var(--text-secondary); font-style: italic;">Awaiting submissions...</span>';
        } else {
            const sorted = [...rawScores].sort((a, b) => a - b);
            scoreBucket.innerHTML = sorted.map(s => `<div class="score-pill">${s}</div>`).join('');
        }
    }

    // ── Histogram ──
    if (data.histogram_json) {
        const histData = JSON.parse(data.histogram_json);
        histogramChart.data.labels = histData.labels;
        histogramChart.data.datasets[0].data = histData.data;
        histogramChart.update();
    }

    // ── Quartiles ──
    quartilesChart.data.datasets[0].data = [data.q3 || 0, data.median || 0, data.q1 || 0];
    quartilesChart.options.scales.x.max = sessionMaxMarks;
    quartilesChart.update();

    // ── Bell Curve + Grade Table (only for 100-mark Overall Marks exams) ──
    if (sessionMaxMarks === 100 && isOverallMarks && data.std_dev > 0 && data.count > 0 && typeof data.mean === 'number') {
        document.getElementById('relative-grading-container').classList.remove('d-none');
        document.getElementById('maxMarksLabel').textContent = sessionMaxMarks;

        const mu = parseFloat(data.mean);
        const sigma = parseFloat(data.std_dev);

        // Grade boundary calculations
        const boundS = mu + 1.5 * sigma;
        const boundA = mu + 0.5 * sigma;
        const boundB = mu - 0.5 * sigma;
        const boundC = mu - 1.0 * sigma;
        const boundD = mu - 1.5 * sigma;
        const rawBoundE = mu - 2.0 * sigma;
        const boundE = Math.max(40, rawBoundE);

        const gradesConfig = [];
        if (boundS <= 100) gradesConfig.push({ g: 'S', name: 'Outstanding', min: boundS, max: 100, color: '#8b5cf6' });
        gradesConfig.push({ g: 'A', name: 'Excellent', min: boundA, max: Math.min(100, boundS - 0.01), color: '#3b82f6' });
        gradesConfig.push({ g: 'B', name: 'Very Good', min: boundB, max: boundA - 0.01, color: '#10b981' });
        gradesConfig.push({ g: 'C', name: 'Good', min: boundC, max: boundB - 0.01, color: '#f59e0b' });
        gradesConfig.push({ g: 'D', name: 'Average', min: boundD, max: boundC - 0.01, color: '#f97316' });
        if (boundD > 40) gradesConfig.push({ g: 'E', name: 'Pass', min: 40, max: boundD - 0.01, color: '#ec4899' });
        gradesConfig.push({ g: 'F', name: 'Fail', min: 0, max: 39.99, color: '#ef4444' });

        // Normal distribution PDF
        const pdf = (x) => (1 / (sigma * Math.sqrt(2 * Math.PI))) * Math.exp(-0.5 * Math.pow((x - mu) / sigma, 2));

        const datasets = [];

        // Shaded areas under the curve per grade zone
        gradesConfig.forEach(grade => {
            const points = [];
            for (let x = Math.max(0, grade.min); x <= Math.min(100, grade.max); x += 0.5) {
                points.push({ x: x, y: pdf(x) });
            }
            if (points.length === 0) return;
            points.push({ x: Math.min(100, grade.max), y: pdf(Math.min(100, grade.max)) });

            datasets.push({
                label: grade.g,
                data: points,
                backgroundColor: grade.color + '40',
                borderColor: grade.color,
                borderWidth: 2,
                fill: 'origin',
                pointRadius: 0,
            });
        });

        // Scatter student marks on the curve
        const curveScatter = rawScores.map(score => ({ x: score, y: pdf(score) }));
        datasets.push({
            type: 'scatter',
            label: 'Students',
            data: curveScatter,
            backgroundColor: '#ffffff',
            borderColor: '#94a3b8',
            pointRadius: 4,
            pointHoverRadius: 6,
            borderWidth: 1
        });

        if (!bellCurveChart) {
            const bellCtx = document.getElementById('bellCurveChart').getContext('2d');
            bellCurveChart = new Chart(bellCtx, {
                type: 'line',
                data: { datasets: datasets },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: { type: 'linear', min: 0, max: 100, title: { display: true, text: 'Scores' } },
                        y: { display: false }
                    },
                    plugins: {
                        legend: { display: false },
                        tooltip: { filter: (itm) => itm.datasetIndex === datasets.length - 1 }
                    }
                }
            });
        } else {
            bellCurveChart.data.datasets = datasets;
            bellCurveChart.update();
        }

        // ── Grade Table ──
        const tbody = document.getElementById('grade-table-body');
        tbody.innerHTML = '';

        gradesConfig.forEach(g => {
            const count = rawScores.filter(s => s >= g.min && s <= g.max).length;
            tbody.innerHTML += `
            <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                <td style="padding: 0.55rem 0.75rem;">
                    <span style="color: ${g.color}; font-weight: 600;">${g.g} (${g.name})</span>
                </td>
                <td style="padding: 0.55rem 0.75rem; color: var(--text-secondary);">${g.min.toFixed(2)} – ${g.max.toFixed(2)}</td>
            </tr>`;
        });

    } else {
        const c = document.getElementById('relative-grading-container');
        if (c) c.classList.add('d-none');
    }
}

initDashboard();
