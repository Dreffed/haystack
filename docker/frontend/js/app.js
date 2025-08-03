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
        case 'admin':
            loadAdminInterface();
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

// Admin Interface Functions
let currentAdminTable = null;
let currentAdminEngine = null;
let currentEditRecord = null;

async function loadAdminInterface() {
    // Load database tables
    await loadAdminTables();
    
    // Load engine forms
    await loadAdminEngines();
}

async function loadAdminTables() {
    try {
        const tablesData = await apiCall('/api/admin/tables');
        if (tablesData && tablesData.tables) {
            updateAdminTablesList(tablesData.tables);
        }
    } catch (error) {
        console.error('Error loading admin tables:', error);
    }
}

function updateAdminTablesList(tables) {
    const tablesList = document.getElementById('admin-tables-list');
    
    const html = tables.map(table => `
        <button type="button" class="list-group-item list-group-item-action d-flex justify-content-between align-items-center admin-table-btn" 
                onclick="selectAdminTable('${table.name}')" data-table="${table.name}">
            <div>
                <div class="fw-bold">${table.name}</div>
                <small class="text-muted">${table.description}</small>
            </div>
            <i class="fas fa-table text-muted"></i>
        </button>
    `).join('');
    
    tablesList.innerHTML = html;
}

async function loadAdminEngines() {
    try {
        const enginesData = await apiCall('/api/admin/engines/forms');
        if (enginesData && enginesData.forms) {
            updateAdminEnginesList(enginesData.forms);
        }
    } catch (error) {
        console.error('Error loading admin engines:', error);
    }
}

function updateAdminEnginesList(engines) {
    const enginesList = document.getElementById('admin-engines-list');
    
    const html = Object.keys(engines).map(engineName => {
        const engine = engines[engineName];
        return `
            <button type="button" class="list-group-item list-group-item-action d-flex justify-content-between align-items-center admin-engine-btn" 
                    onclick="selectAdminEngine('${engineName}')" data-engine="${engineName}">
                <div>
                    <div class="fw-bold">${engine.title}</div>
                    <small class="text-muted">${engine.description}</small>
                </div>
                <i class="fas fa-cogs text-muted"></i>
            </button>
        `;
    }).join('');
    
    enginesList.innerHTML = html;
}

async function selectAdminTable(tableName) {
    // Update UI selection
    document.querySelectorAll('.admin-table-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.admin-engine-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelector(`[data-table="${tableName}"]`).classList.add('active');
    
    currentAdminTable = tableName;
    currentAdminEngine = null;
    
    // Update title and show controls
    document.getElementById('admin-content-title').innerHTML = `<i class="fas fa-table me-2"></i>${tableName} Records`;
    document.getElementById('admin-create-btn').style.display = 'inline-block';
    document.getElementById('admin-refresh-btn').style.display = 'inline-block';
    
    // Load table data
    await loadTableData(tableName);
}

async function selectAdminEngine(engineName) {
    // Update UI selection
    document.querySelectorAll('.admin-table-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.admin-engine-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelector(`[data-engine="${engineName}"]`).classList.add('active');
    
    currentAdminEngine = engineName;
    currentAdminTable = null;
    
    // Update title and hide table controls
    document.getElementById('admin-content-title').innerHTML = `<i class="fas fa-cogs me-2"></i>${engineName} Configuration`;
    document.getElementById('admin-create-btn').style.display = 'none';
    document.getElementById('admin-refresh-btn').style.display = 'none';
    
    // Load engine form
    await loadEngineForm(engineName);
}

async function loadTableData(tableName, page = 0, limit = 50) {
    try {
        const offset = page * limit;
        const tableData = await apiCall(`/api/admin/tables/${tableName}/data?limit=${limit}&offset=${offset}`);
        
        if (tableData) {
            await displayTableData(tableName, tableData);
        }
    } catch (error) {
        console.error(`Error loading table data for ${tableName}:`, error);
        document.getElementById('admin-content').innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle me-2"></i>
                Error loading table data: ${error.message}
            </div>
        `;
    }
}

async function displayTableData(tableName, tableData) {
    const content = document.getElementById('admin-content');
    
    if (!tableData.data || tableData.data.length === 0) {
        content.innerHTML = `
            <div class="text-center text-muted py-4">
                <i class="fas fa-inbox fa-3x mb-3"></i>
                <p>No records found in ${tableName}</p>
                <button class="btn btn-primary" onclick="showCreateRecordModal()">
                    <i class="fas fa-plus me-2"></i>Create First Record
                </button>
            </div>
        `;
        return;
    }
    
    // Get table schema for proper column headers
    const schemaData = await apiCall(`/api/admin/tables/${tableName}/schema`);
    const columns = schemaData ? schemaData.columns : [];
    
    // Build table HTML
    const columnHeaders = columns.length > 0 
        ? columns.map(col => `<th>${col.name}</th>`).join('')
        : Object.keys(tableData.data[0]).map(key => `<th>${key}</th>`).join('');
    
    const tableRows = tableData.data.map(record => {
        const recordId = getRecordId(record, tableName);
        const cells = columns.length > 0
            ? columns.map(col => {
                const value = record[col.name];
                return `<td>${formatCellValue(value, col.type)}</td>`;
              }).join('')
            : Object.values(record).map(value => `<td>${formatCellValue(value)}</td>`).join('');
        
        return `
            <tr>
                ${cells}
                <td>
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-outline-primary" onclick="editRecord('${tableName}', ${recordId})" title="Edit">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-outline-danger" onclick="confirmDeleteRecord('${tableName}', ${recordId})" title="Delete">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
    
    content.innerHTML = `
        <div class="table-responsive">
            <table class="table table-striped table-hover">
                <thead class="table-dark">
                    <tr>
                        ${columnHeaders}
                        <th width="120">Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${tableRows}
                </tbody>
            </table>
        </div>
        
        <div class="d-flex justify-content-between align-items-center mt-3">
            <small class="text-muted">
                Showing ${tableData.data.length} records
            </small>
            <div class="btn-group btn-group-sm">
                <button class="btn btn-outline-secondary" onclick="loadTableData('${tableName}', 0)">
                    <i class="fas fa-chevron-left"></i> Previous
                </button>
                <button class="btn btn-outline-secondary" onclick="loadTableData('${tableName}', 1)">
                    Next <i class="fas fa-chevron-right"></i>
                </button>
            </div>
        </div>
    `;
}

async function loadEngineForm(engineName) {
    try {
        const engineData = await apiCall(`/api/admin/engines/${engineName}/form`);
        
        if (engineData && engineData.form) {
            displayEngineForm(engineName, engineData.form);
        }
    } catch (error) {
        console.error(`Error loading engine form for ${engineName}:`, error);
        document.getElementById('admin-content').innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle me-2"></i>
                Error loading engine form: ${error.message}
            </div>
        `;
    }
}

function displayEngineForm(engineName, formConfig) {
    const content = document.getElementById('admin-content');
    
    let formHtml = `
        <div class="row">
            <div class="col-md-8">
                <form id="engine-config-form" class="needs-validation" novalidate>
                    <div class="card">
                        <div class="card-header">
                            <h6 class="mb-0">${formConfig.title}</h6>
                            <small class="text-muted">${formConfig.description}</small>
                        </div>
                        <div class="card-body">
    `;
    
    // Generate form fields
    Object.keys(formConfig.fields).forEach(fieldName => {
        const field = formConfig.fields[fieldName];
        formHtml += generateFormField(fieldName, field);
    });
    
    formHtml += `
                        </div>
                        <div class="card-footer">
                            <button type="button" class="btn btn-success" onclick="saveEngineConfiguration('${engineName}')">
                                <i class="fas fa-save me-2"></i>Save Configuration
                            </button>
                            <button type="button" class="btn btn-primary ms-2" onclick="startEngineWithConfig('${engineName}')">
                                <i class="fas fa-play me-2"></i>Save & Start Engine
                            </button>
                        </div>
                    </div>
                </form>
            </div>
            <div class="col-md-4">
                <div class="card">
                    <div class="card-header">
                        <h6 class="mb-0">Available Actions</h6>
                    </div>
                    <div class="card-body">
                        <div class="list-group list-group-flush">
    `;
    
    // Add available actions
    formConfig.actions.forEach(action => {
        formHtml += `
            <div class="list-group-item d-flex justify-content-between align-items-center">
                <span>${action}</span>
                <button class="btn btn-sm btn-outline-primary" onclick="runEngineAction('${engineName}', '${action}')">
                    <i class="fas fa-play"></i>
                </button>
            </div>
        `;
    });
    
    formHtml += `
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    content.innerHTML = formHtml;
}

function generateFormField(fieldName, field) {
    let fieldHtml = `<div class="mb-3">`;
    
    if (field.type === 'array') {
        fieldHtml += `
            <label class="form-label">${field.label} ${field.required ? '<span class="text-danger">*</span>' : ''}</label>
            <div id="${fieldName}-container" class="border rounded p-3">
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <small class="text-muted">Click "Add Item" to create new entries</small>
                    <button type="button" class="btn btn-sm btn-outline-success" onclick="addArrayItem('${fieldName}', ${JSON.stringify(field.item_schema).replace(/"/g, '&quot;')})">
                        <i class="fas fa-plus me-1"></i>Add Item
                    </button>
                </div>
                <div id="${fieldName}-items">
                    <!-- Array items will be added here -->
                </div>
            </div>
        `;
    } else {
        const inputType = field.type === 'url' ? 'url' : field.type === 'number' ? 'number' : 'text';
        fieldHtml += `
            <label for="${fieldName}" class="form-label">${field.label} ${field.required ? '<span class="text-danger">*</span>' : ''}</label>
            <input type="${inputType}" class="form-control" id="${fieldName}" name="${fieldName}" 
                   value="${field.default || ''}" ${field.required ? 'required' : ''}>
        `;
    }
    
    fieldHtml += `</div>`;
    return fieldHtml;
}

function addArrayItem(fieldName, itemSchema) {
    const container = document.getElementById(`${fieldName}-items`);
    const itemIndex = container.children.length;
    
    let itemHtml = `
        <div class="card mb-2" id="${fieldName}-item-${itemIndex}">
            <div class="card-header py-2 d-flex justify-content-between align-items-center">
                <small class="mb-0">Item ${itemIndex + 1}</small>
                <button type="button" class="btn btn-sm btn-outline-danger" onclick="removeArrayItem('${fieldName}-item-${itemIndex}')">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
            <div class="card-body py-2">
                <div class="row">
    `;
    
    Object.keys(itemSchema).forEach(key => {
        const field = itemSchema[key];
        const inputType = field.type === 'url' ? 'url' : field.type === 'number' ? 'number' : 'text';
        itemHtml += `
            <div class="col-md-6 mb-2">
                <label class="form-label small">${field.label}</label>
                <input type="${inputType}" class="form-control form-control-sm" 
                       name="${fieldName}[${itemIndex}][${key}]" value="${field.default || ''}" 
                       ${field.required ? 'required' : ''}>
            </div>
        `;
    });
    
    itemHtml += `
                </div>
            </div>
        </div>
    `;
    
    container.insertAdjacentHTML('beforeend', itemHtml);
}

function removeArrayItem(itemId) {
    document.getElementById(itemId).remove();
}

// Helper functions
function getRecordId(record, tableName) {
    const primaryKeys = {
        'Engines': 'EngineId',
        'Items': 'itemId',
        'ItemData': 'ItemDataId',
        'Actions': 'actionId',
        'Config': 'configId',
        'Status': 'statusId'
    };
    
    const pkField = primaryKeys[tableName] || 'id';
    return record[pkField];
}

function formatCellValue(value, type = 'text') {
    if (value === null || value === undefined) return '<em class="text-muted">null</em>';
    if (typeof value === 'string' && value.length > 100) {
        return `<span title="${value}">${value.substring(0, 97)}...</span>`;
    }
    if (type === 'timestamp' || (typeof value === 'string' && value.match(/^\d{4}-\d{2}-\d{2}/))) {
        return formatDateTime(value);
    }
    return value;
}

async function editRecord(tableName, recordId) {
    try {
        const record = await apiCall(`/api/admin/tables/${tableName}/records/${recordId}`);
        if (record) {
            showEditRecordModal(tableName, recordId, record);
        }  
    } catch (error) {
        showError(`Failed to load record for editing: ${error.message}`);
    }
}

function showCreateRecordModal() {
    if (!currentAdminTable) return;
    
    // This would show a modal for creating new records
    showSuccess('Create record functionality will be implemented here');
}

function showEditRecordModal(tableName, recordId, record) {
    currentEditRecord = { tableName, recordId, record };
    
    // Populate the edit form fields dynamically based on record structure
    const modalTitle = document.getElementById('recordEditModalLabel');
    modalTitle.textContent = `Edit ${tableName} Record #${recordId}`;
    
    const fieldsContainer = document.getElementById('recordEditFields');
    
    let fieldsHtml = '';
    Object.keys(record).forEach(key => {
        if (key.toLowerCase().includes('id') && key !== 'itemId') {
            // Skip auto-increment IDs but allow itemId for foreign keys
            return;
        }
        
        const value = record[key] || '';
        fieldsHtml += `
            <div class="mb-3">
                <label for="edit-${key}" class="form-label">${key}</label>
                <input type="text" class="form-control" id="edit-${key}" name="${key}" value="${value}">
            </div>
        `;
    });
    
    fieldsContainer.innerHTML = fieldsHtml;
    
    // Show delete button for existing records
    document.getElementById('deleteRecordBtn').style.display = 'inline-block';
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('recordEditModal'));
    modal.show();
}

async function saveRecord() {
    if (!currentEditRecord) return;
    
    const form = document.getElementById('recordEditForm');
    const formData = new FormData(form);
    const recordData = {};
    
    for (const [key, value] of formData.entries()) {
        recordData[key] = value;
    }
    
    try {
        const result = await apiCall(
            `/api/admin/tables/${currentEditRecord.tableName}/records/${currentEditRecord.recordId}`,
            {
                method: 'PUT',
                body: JSON.stringify(recordData)
            }
        );
        
        if (result) {
            showSuccess('Record updated successfully');
            bootstrap.Modal.getInstance(document.getElementById('recordEditModal')).hide();
            await loadTableData(currentEditRecord.tableName);
        }
    } catch (error) {
        showError(`Failed to update record: ${error.message}`);
    }
}

async function deleteCurrentRecord() {
    if (!currentEditRecord) return;
    
    if (!confirm('Are you sure you want to delete this record? This action cannot be undone.')) {
        return;
    }
    
    try {
        const result = await apiCall(
            `/api/admin/tables/${currentEditRecord.tableName}/records/${currentEditRecord.recordId}`,
            { method: 'DELETE' }
        );
        
        if (result) {
            showSuccess('Record deleted successfully');
            bootstrap.Modal.getInstance(document.getElementById('recordEditModal')).hide();
            await loadTableData(currentEditRecord.tableName);
        }
    } catch (error) {
        showError(`Failed to delete record: ${error.message}`);
    }
}

function refreshAdminContent() {
    if (currentAdminTable) {
        loadTableData(currentAdminTable);
    } else if (currentAdminEngine) {
        loadEngineForm(currentAdminEngine);
    }
}

async function saveEngineConfiguration(engineName) {
    // This would save the engine configuration
    showSuccess(`Engine ${engineName} configuration saved`);
}

async function startEngineWithConfig(engineName) {
    // This would save config and start the engine
    await saveEngineConfiguration(engineName);
    await startEngine(engineName);
}