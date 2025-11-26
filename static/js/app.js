// API Configuration
const API_BASE = '';

// State
let autoRefresh = true;
let refreshInterval = null;

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
    startAutoRefresh();
});

function initializeApp() {
    loadSummaries();
    loadAlerts();
    loadChatHistory();

    // Set up event listeners
    document.getElementById('refresh-summaries')?.addEventListener('click', loadSummaries);
    document.getElementById('refresh-alerts')?.addEventListener('click', loadAlerts);
    document.getElementById('send-chat')?.addEventListener('click', sendChatMessage);
    document.getElementById('chat-input')?.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendChatMessage();
    });
}

function startAutoRefresh() {
    if (refreshInterval) clearInterval(refreshInterval);

    refreshInterval = setInterval(() => {
        if (autoRefresh) {
            loadSummaries();
            loadAlerts();
        }
    }, 30000); // Refresh every 30 seconds
}

// Log Summaries
async function loadSummaries() {
    try {
        const response = await fetch(`${API_BASE}/api/logs/summaries?limit=10`);
        const data = await response.json();

        displaySummaries(data);
    } catch (error) {
        console.error('Error loading summaries:', error);
        showError('summaries-list', 'Failed to load log summaries');
    }
}

function displaySummaries(summaries) {
    const container = document.getElementById('summaries-list');

    if (!summaries || summaries.length === 0) {
        container.innerHTML = '<div class="empty-state">No log summaries available</div>';
        return;
    }

    container.innerHTML = summaries.map(summary => `
        <div class="summary-item">
            <div class="summary-header">
                <span class="summary-time">${formatTime(summary.start_time)} - ${formatTime(summary.end_time)}</span>
            </div>
            <div class="summary-stats">
                <span class="stat">📝 ${summary.total_logs} logs</span>
                <span class="stat">❌ ${summary.error_count} errors</span>
                <span class="stat">⚠️ ${summary.warning_count} warnings</span>
            </div>
            <div class="summary-text">${summary.summary_text}</div>
            ${summary.anomalies && summary.anomalies.length > 0 ?
            `<div class="summary-anomalies" style="margin-top: 0.5rem; padding: 0.5rem; background: rgba(239, 68, 68, 0.1); border-radius: 0.5rem; font-size: 0.875rem;">
                    ⚠️ ${summary.anomalies.length} anomalies detected
                </div>` : ''}
        </div>
    `).join('');
}

// Alerts
async function loadAlerts() {
    try {
        const response = await fetch(`${API_BASE}/api/alerts?limit=20`);
        const data = await response.json();

        displayAlerts(data.alerts);
        updateAlertStats(data.alerts);
    } catch (error) {
        console.error('Error loading alerts:', error);
        showError('alerts-list', 'Failed to load alerts');
    }
}

function displayAlerts(alerts) {
    const container = document.getElementById('alerts-list');

    if (!alerts || alerts.length === 0) {
        container.innerHTML = '<div class="empty-state">No alerts</div>';
        return;
    }

    container.innerHTML = alerts.map(alert => `
        <div class="alert-item ${alert.severity}">
            <div class="alert-header">
                <div class="alert-title">${alert.title}</div>
                <span class="severity-badge ${alert.severity}">${alert.severity}</span>
            </div>
            <div class="alert-meta">
                <span>📅 ${formatDateTime(alert.timestamp)}</span>
                <span>📂 ${alert.category}</span>
                <span>📊 Priority: ${(alert.priority_score * 100).toFixed(0)}%</span>
                <span>🏷️ ${alert.status}</span>
            </div>
            ${alert.description ? `<div class="alert-description">${alert.description}</div>` : ''}
        </div>
    `).join('');
}

function updateAlertStats(alerts) {
    const critical = alerts.filter(a => a.severity === 'critical' && a.status === 'open').length;
    const badge = document.querySelector('.status-badge');

    if (badge && critical > 0) {
        badge.innerHTML = `<span class="status-dot" style="background: var(--critical);"></span>${critical} Critical Alerts`;
    }
}

// Chat
async function sendChatMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();

    if (!message) return;

    // Clear input
    input.value = '';

    // Add user message to UI
    addChatMessage(message, 'user');

    try {
        const response = await fetch(`${API_BASE}/api/chat/message`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message })
        });

        const data = await response.json();

        // Add bot response to UI
        addChatMessage(data.bot_response, 'bot');
    } catch (error) {
        console.error('Error sending message:', error);
        addChatMessage('❌ Error: Could not process message', 'bot');
    }
}

function addChatMessage(message, type) {
    const container = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'chat-message';

    const contentDiv = document.createElement('div');
    contentDiv.className = type === 'user' ? 'user-message' : 'bot-message';
    contentDiv.textContent = message;

    messageDiv.appendChild(contentDiv);
    container.appendChild(messageDiv);

    // Scroll to bottom
    container.scrollTop = container.scrollHeight;
}

async function loadChatHistory() {
    try {
        const response = await fetch(`${API_BASE}/api/chat/history?limit=20`);
        const data = await response.json();

        const container = document.getElementById('chat-messages');
        container.innerHTML = '';

        // Reverse to show oldest first
        const messages = data.messages.reverse();

        messages.forEach(msg => {
            addChatMessage(msg.user_message, 'user');
            addChatMessage(msg.bot_response, 'bot');
        });
    } catch (error) {
        console.error('Error loading chat history:', error);
    }
}

// Utility Functions
function formatTime(isoString) {
    const date = new Date(isoString);
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
}

function formatDateTime(isoString) {
    const date = new Date(isoString);
    const today = new Date();

    if (date.toDateString() === today.toDateString()) {
        return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    } else {
        return date.toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }
}

function showError(containerId, message) {
    const container = document.getElementById(containerId);
    container.innerHTML = `<div class="empty-state" style="color: var(--error);">${message}</div>`;
}

// Generate Summary
async function generateSummary() {
    try {
        const response = await fetch(`${API_BASE}/api/logs/summarize`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ hours: 1 })
        });

        if (response.ok) {
            loadSummaries();
        }
    } catch (error) {
        console.error('Error generating summary:', error);
    }
}

// Filter alerts
function filterAlerts(severity) {
    loadAlerts(`?severity=${severity}`);
}
