// Haystack Web Collector UI JavaScript

// Configuration
const API_BASE_URL = window.location.protocol + '//' + window.location.hostname + ':8000';
let currentPage = 0;
const itemsPerPage = 20;

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    // Show dashboard by default
    showSection('dashboard');
    
    // Load initial data
    refreshDashboard();
    
    // Set up periodic refresh
    setInterval(refreshDashboard, 30000); // Refresh every 30 seconds
});

// Navigation functions
function showSection(sectionName) {
    // Hide all sections
    document.querySelectorAll('.content-section').forEach(section => {
        section.style.display = 'none';
    });
    
    // Show selected section
    const section = document.getElementById(sectionName);
    if (section) {
        section.style.display = 'block';
    }
    
    // Update navbar active state
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    document.querySelector(`[href="#${sectionName}"]`).classList.add('active');
    
    // Load section-specific data
    switch(sectionName) {
        case 'dashboard':
            refreshDashboard();
            break;
        case 'engines':
            refreshEngines();
            break;
        case 'items':
            refreshItems();
            break;
        case 'status':
            refreshStatus();
            break;
        case 'config':
            loadConfig();
            break;
    }
}

// API helper functions
async function apiCall(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error(`API call failed for ${endpoint}:`, error);
        showError(`Failed to connect to backend API: ${error.message}`);
        return null;
    }
}

// Dashboard functions
async function refreshDashboard() {
    try {
        // Get system health
        const health = await apiCall('/health');
        if (health) {
            updateDashboardStats(health);
        }
        
        // Get recent activity
        const status = await apiCall('/api/status?limit=10');
        if (status) {
            updateActivityLog(status);
        }
    } catch (error) {
        console.error('Error refreshing dashboard:', error);
    }
}

function updateDashboardStats(health) {
    document.getElementById('active-engines').textContent = health.active_engines || 0;
    document.getElementById('total-items').textContent = health.total_items || 0;
    document.getElementById('pending-jobs').textContent = health.pending_jobs || 0;
    
    const statusElement = document.getElementById('system-status');
    statusElement.textContent = health.status || 'Unknown';
    
    // Update status indicator
    const statusCard = statusElement.closest('.card');
    statusCard.className = statusCard.className.replace(/bg-(success|danger|warning)/, '');
    
    if (health.status === 'healthy') {
        statusCard.classList.add('bg-success');
    } else if (health.status === 'unhealthy') {
        statusCard.classList.add('bg-danger');
    } else {
        statusCard.classList.add('bg-warning');
    }
}

function updateActivityLog(statusList) {
    const activityLog = document.getElementById('activity-log');
    
    if (!statusList || statusList.length === 0) {
        activityLog.innerHTML = '<p class="text-muted">No recent activity</p>';
        return;
    }
    
    const html = statusList.map(status => `
        <div class="activity-item">
            <div class="activity-time">${formatTime(status.timestamp)}</div>
            <div class="activity-message">${status.message}</div>
        </div>
    `).join('');
    
    activityLog.innerHTML = html;
}

// Engine management functions
async function refreshEngines() {
    const engines = await apiCall('/api/engines');
    updateEnginesTable(engines || []);
}

function updateEnginesTable(engines) {
    const tbody = document.getElementById('engines-table');
    
    if (engines.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">No engines found</td></tr>';
        return;
    }
    
    const html = engines.map(engine => `
        <tr>
            <td><strong>${engine.name}</strong></td>
            <td>${engine.version}</td>
            <td><span class="engine-status ${engine.disabled ? 'stopped' : 'idle'}">${engine.disabled ? 'Disabled' : 'Ready'}</span></td>
            <td>${formatDate(engine.created)}</td>
            <td>
                <button class="btn btn-sm btn-success me-1" onclick="startEngine('${engine.name}')" ${engine.disabled ? 'disabled' : ''}>
                    <i class="fas fa-play"></i> Start
                </button>
                <button class="btn btn-sm btn-danger" onclick="stopEngine('${engine.name}')">
                    <i class="fas fa-stop"></i> Stop
                </button>
            </td>
        </tr>
    `).join('');
    
    tbody.innerHTML = html;
}

async function startEngine(engineName) {
    const button = event.target;
    const originalHtml = button.innerHTML;
    
    button.innerHTML = '<span class="spinner"></span> Starting...';
    button.disabled = true;
    
    try {
        const result = await apiCall(`/api/engines/${engineName}/start`, { method: 'POST' });
        if (result) {
            showSuccess(`Engine ${engineName} started successfully`);
            setTimeout(refreshEngines, 2000); // Refresh after 2 seconds
        }
    } catch (error) {
        showError(`Failed to start engine ${engineName}`);
    } finally {
        button.innerHTML = originalHtml;
        button.disabled = false;
    }
}

async function stopEngine(engineName) {
    try {
        const result = await apiCall(`/api/engines/${engineName}/stop`, { method: 'POST' });
        if (result) {
            showSuccess(`Engine ${engineName} stopped successfully`);
            setTimeout(refreshEngines, 1000);
        }
    } catch (error) {
        showError(`Failed to stop engine ${engineName}`);
    }
}

// Items management functions
async function refreshItems() {
    const offset = currentPage * itemsPerPage;
    const items = await apiCall(`/api/items?limit=${itemsPerPage}&offset=${offset}`);
    updateItemsTable(items || []);
}

function updateItemsTable(items) {
    const tbody = document.getElementById('items-table');
    
    if (items.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">No items found</td></tr>';
        return;
    }
    
    const html = items.map(item => `
        <tr>
            <td>${item.item_id}</td>
            <td><a href="${item.uri}" target="_blank" class="text-truncate" style="max-width: 300px; display: inline-block;">${item.uri}</a></td>
            <td>Engine ${item.engine_id}</td>
            <td>${formatDate(item.created)}</td>
            <td>
                <button class="btn btn-sm btn-outline-primary" onclick="viewItem(${item.item_id})">
                    <i class="fas fa-eye"></i> View
                </button>
            </td>
        </tr>
    `).join('');
    
    tbody.innerHTML = html;
}

async function viewItem(itemId) {
    try {
        const item = await apiCall(`/api/items/${itemId}`);
        if (item) {
            showItemModal(item);
        }
    } catch (error) {
        showError(`Failed to load item ${itemId}`);
    }
}

function showItemModal(item) {
    // Create modal HTML
    const modalHtml = `
        <div class="modal fade" id="itemModal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Item ${item.item_id}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p><strong>URI:</strong> <a href="${item.uri}" target="_blank">${item.uri}</a></p>
                        <h6>Data:</h6>
                        <div class="table-responsive">
                            <table class="table table-sm">
                                <thead>
                                    <tr><th>Type</th><th>Value</th></tr>
                                </thead>
                                <tbody>
                                    ${item.data.map(d => `<tr><td>${d.type}</td><td>${d.value}</td></tr>`).join('')}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal
    const existingModal = document.getElementById('itemModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Add new modal
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('itemModal'));
    modal.show();
}

// Status functions
async function refreshStatus() {
    const status = await apiCall('/api/status?limit=50');
    updateStatusLog(status || []);
}

function updateStatusLog(statusList) {
    const statusLog = document.getElementById('status-log');
    
    if (statusList.length === 0) {
        statusLog.innerHTML = '<p class="text-muted">No status messages found</p>';
        return;
    }
    
    const html = statusList.map(status => `
        <div class="status-item">
            <div class="status-meta">
                Engine ${status.engine_id} • Action ${status.action_id} • ${formatDateTime(status.timestamp)}
            </div>
            <div class="status-message">${status.message}</div>
        </div>
    `).join('');
    
    statusLog.innerHTML = html;
}

// Configuration functions
async function loadConfig() {
    const config = await apiCall('/api/config');
    updateConfigForm(config || {});
}

function updateConfigForm(config) {
    const configForm = document.getElementById('config-form');
    
    const configItems = [
        { key: 'RunQueue', label: 'Run Queue', type: 'select', options: [{ value: '0', text: 'Disabled' }, { value: '1', text: 'Enabled' }] },
        { key: 'MaxConcurrentJobs', label: 'Max Concurrent Jobs', type: 'number' },
        { key: 'DefaultDelay', label: 'Default Delay (seconds)', type: 'number' }
    ];
    
    const html = configItems.map(item => {
        const value = config[item.key] || '';
        let input;
        
        if (item.type === 'select') {
            const options = item.options.map(opt => 
                `<option value="${opt.value}" ${opt.value === value ? 'selected' : ''}>${opt.text}</option>`
            ).join('');
            input = `<select class="form-control config-value" data-key="${item.key}">${options}</select>`;
        } else {
            input = `<input type="${item.type}" class="form-control config-value" value="${value}" data-key="${item.key}">`;
        }
        
        return `
            <div class="config-item">
                <div class="config-label">${item.label}</div>
                ${input}
                <div class="config-actions">
                    <button class="btn btn-sm btn-primary" onclick="updateConfigValue('${item.key}')">
                        <i class="fas fa-save"></i> Save
                    </button>
                </div>
            </div>
        `;
    }).join('');
    
    configForm.innerHTML = html;
}

async function updateConfigValue(key) {
    const input = document.querySelector(`[data-key="${key}"]`);
    const value = input.value;
    
    try {
        const result = await apiCall(`/api/config/${key}`, {
            method: 'PUT',
            body: JSON.stringify({ value: value })
        });
        
        if (result) {
            showSuccess(`Configuration ${key} updated successfully`);
        }
    } catch (error) {
        showError(`Failed to update configuration ${key}`);
    }
}

// Utility functions
function formatTime(timestamp) {
    return new Date(timestamp).toLocaleTimeString();
}

function formatDate(timestamp) {
    return new Date(timestamp).toLocaleDateString();
}

function formatDateTime(timestamp) {
    return new Date(timestamp).toLocaleString();
}

function showSuccess(message) {
    showToast(message, 'success');
}

function showError(message) {
    showToast(message, 'danger');
}

function showToast(message, type) {
    // Create toast HTML
    const toastHtml = `
        <div class="toast align-items-center text-white bg-${type} border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;
    
    // Create toast container if it doesn't exist
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        toastContainer.style.zIndex = '1055';
        document.body.appendChild(toastContainer);
    }
    
    // Add toast
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    
    // Show toast
    const toastElement = toastContainer.lastElementChild;
    const toast = new bootstrap.Toast(toastElement, { delay: 5000 });
    toast.show();
    
    // Remove toast element after it's hidden
    toastElement.addEventListener('hidden.bs.toast', () => {
        toastElement.remove();
    });
}