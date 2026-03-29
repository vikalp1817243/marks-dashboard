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
}

initDashboard();
