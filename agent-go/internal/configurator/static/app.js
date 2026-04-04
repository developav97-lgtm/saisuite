// Saicloud Agent Configurator - Frontend Application
// Handles CRUD for connections and connection testing.

const API_BASE = '/api';
let editingId = null;

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
    loadStatus();
    loadConnections();
});

// --- API Helpers ---

async function apiFetch(path, options = {}) {
    const resp = await fetch(API_BASE + path, {
        headers: { 'Content-Type': 'application/json' },
        ...options,
    });
    const data = await resp.json();
    if (!resp.ok && !data.success) {
        throw new Error(data.error || `HTTP ${resp.status}`);
    }
    return data;
}

// --- Status ---

async function loadStatus() {
    try {
        const resp = await apiFetch('/status');
        const s = resp.data;
        document.getElementById('agent-version').textContent = 'v' + s.version;
        document.getElementById('total-connections').textContent = s.total_connections;
        document.getElementById('enabled-connections').textContent = s.enabled_count;
        document.getElementById('log-level').textContent = s.log_level;
    } catch (err) {
        console.error('Failed to load status:', err);
    }
}

// --- Connections ---

async function loadConnections() {
    try {
        const resp = await apiFetch('/connections');
        renderConnections(resp.data || []);
    } catch (err) {
        console.error('Failed to load connections:', err);
        document.getElementById('connections-list').innerHTML =
            '<div class="empty-state"><p>Error loading connections</p></div>';
    }
}

function renderConnections(connections) {
    const container = document.getElementById('connections-list');

    if (!connections.length) {
        container.innerHTML = `
            <div class="empty-state">
                <p>No connections configured yet.</p>
                <button class="btn btn-primary" onclick="showCreateForm()">+ Add First Connection</button>
            </div>`;
        return;
    }

    container.innerHTML = connections.map(conn => {
        const statusClass = conn.enabled ? 'enabled' : 'disabled';
        const statusText = conn.enabled ? 'Enabled' : 'Disabled';
        const lastConteo = conn.sync.last_conteo_gl || 0;
        const lastAcct = conn.sync.last_sync_acct ? new Date(conn.sync.last_sync_acct).toLocaleString() : 'Never';
        const lastCust = conn.sync.last_sync_cust ? new Date(conn.sync.last_sync_cust).toLocaleString() : 'Never';

        return `
            <div class="connection-card ${statusClass}">
                <div class="card-header">
                    <div>
                        <div class="card-title">${escapeHtml(conn.name)}</div>
                        <div class="card-id">${escapeHtml(conn.id)}</div>
                    </div>
                    <span class="card-status ${statusClass}">${statusText}</span>
                </div>
                <div class="card-details">
                    <div class="detail-group">
                        <label>Firebird Database</label>
                        <span>${escapeHtml(conn.firebird.database)}</span>
                    </div>
                    <div class="detail-group">
                        <label>Saicloud API</label>
                        <span>${escapeHtml(conn.saicloud.api_url)}</span>
                    </div>
                    <div class="detail-group">
                        <label>Last GL CONTEO</label>
                        <span>${lastConteo.toLocaleString()}</span>
                    </div>
                    <div class="detail-group">
                        <label>GL Interval / Batch Size</label>
                        <span>${conn.sync.gl_interval_minutes}min / ${conn.sync.batch_size}</span>
                    </div>
                    <div class="detail-group">
                        <label>Last ACCT Sync</label>
                        <span>${lastAcct}</span>
                    </div>
                    <div class="detail-group">
                        <label>Last CUST Sync</label>
                        <span>${lastCust}</span>
                    </div>
                </div>
                <div class="card-actions">
                    <button class="btn btn-success btn-sm" onclick="testConnection('${escapeHtml(conn.id)}')">Test</button>
                    <button class="btn btn-secondary btn-sm" onclick="editConnection('${escapeHtml(conn.id)}')">Edit</button>
                    <button class="btn btn-danger btn-sm" onclick="deleteConnection('${escapeHtml(conn.id)}', '${escapeHtml(conn.name)}')">Delete</button>
                </div>
            </div>`;
    }).join('');
}

// --- Create / Edit ---

function showCreateForm() {
    editingId = null;
    document.getElementById('modal-title').textContent = 'New Connection';
    document.getElementById('conn-id').disabled = false;
    clearForm();
    openModal();
}

async function editConnection(id) {
    try {
        const resp = await apiFetch(`/connections/${id}`);
        const conn = resp.data;
        editingId = id;

        document.getElementById('modal-title').textContent = 'Edit Connection';
        document.getElementById('conn-id').value = conn.id;
        document.getElementById('conn-id').disabled = true;
        document.getElementById('conn-name').value = conn.name;
        document.getElementById('conn-enabled').checked = conn.enabled;
        document.getElementById('fb-host').value = conn.firebird.host;
        document.getElementById('fb-port').value = conn.firebird.port;
        document.getElementById('fb-database').value = conn.firebird.database;
        document.getElementById('fb-user').value = conn.firebird.user;
        document.getElementById('fb-password').value = conn.firebird.password;
        document.getElementById('sc-url').value = conn.saicloud.api_url;
        document.getElementById('sc-company').value = conn.saicloud.company_id;
        document.getElementById('sc-token').value = conn.saicloud.agent_token;
        document.getElementById('sync-gl-interval').value = conn.sync.gl_interval_minutes;
        document.getElementById('sync-ref-interval').value = conn.sync.reference_interval_hours;
        document.getElementById('sync-batch-size').value = conn.sync.batch_size;

        openModal();
    } catch (err) {
        alert('Error loading connection: ' + err.message);
    }
}

async function saveConnection(event) {
    event.preventDefault();

    const conn = {
        id: document.getElementById('conn-id').value.trim(),
        name: document.getElementById('conn-name').value.trim(),
        enabled: document.getElementById('conn-enabled').checked,
        firebird: {
            host: document.getElementById('fb-host').value.trim() || 'localhost',
            port: parseInt(document.getElementById('fb-port').value) || 3050,
            database: document.getElementById('fb-database').value.trim(),
            user: document.getElementById('fb-user').value.trim() || 'SYSDBA',
            password: document.getElementById('fb-password').value.trim() || 'masterkey',
        },
        saicloud: {
            api_url: document.getElementById('sc-url').value.trim(),
            company_id: document.getElementById('sc-company').value.trim(),
            agent_token: document.getElementById('sc-token').value.trim(),
        },
        sync: {
            gl_interval_minutes: parseInt(document.getElementById('sync-gl-interval').value) || 15,
            reference_interval_hours: parseInt(document.getElementById('sync-ref-interval').value) || 24,
            batch_size: parseInt(document.getElementById('sync-batch-size').value) || 500,
            last_conteo_gl: 0,
        },
    };

    try {
        if (editingId) {
            await apiFetch(`/connections/${editingId}`, {
                method: 'PUT',
                body: JSON.stringify(conn),
            });
        } else {
            await apiFetch('/connections', {
                method: 'POST',
                body: JSON.stringify(conn),
            });
        }
        closeModal();
        loadConnections();
        loadStatus();
    } catch (err) {
        alert('Error saving connection: ' + err.message);
    }
}

async function deleteConnection(id, name) {
    if (!confirm(`Are you sure you want to delete "${name}" (${id})?`)) return;

    try {
        await apiFetch(`/connections/${id}`, { method: 'DELETE' });
        loadConnections();
        loadStatus();
    } catch (err) {
        alert('Error deleting connection: ' + err.message);
    }
}

// --- Test Connection ---

async function testConnection(id) {
    const resultsDiv = document.getElementById('test-results');
    resultsDiv.innerHTML = '<p class="loading">Testing connection, please wait...</p>';
    document.getElementById('test-modal').style.display = 'flex';

    try {
        const resp = await apiFetch(`/connections/${id}/test`, { method: 'POST' });
        const r = resp.data;

        let html = '';

        // Firebird result
        html += `
            <div class="test-result-item ${r.firebird_ok ? 'success' : 'error'}">
                <span class="test-icon">${r.firebird_ok ? '&#10003;' : '&#10007;'}</span>
                <div class="test-detail">
                    <div class="label">Firebird Database</div>
                    <div class="message">${escapeHtml(r.firebird_msg)}</div>
                </div>
            </div>`;

        // Saicloud result
        html += `
            <div class="test-result-item ${r.saicloud_ok ? 'success' : 'error'}">
                <span class="test-icon">${r.saicloud_ok ? '&#10003;' : '&#10007;'}</span>
                <div class="test-detail">
                    <div class="label">Saicloud API</div>
                    <div class="message">${escapeHtml(r.saicloud_msg)}</div>
                </div>
            </div>`;

        // Stats (only if Firebird connected)
        if (r.firebird_ok) {
            html += `
                <div class="test-stats">
                    <div class="stat-row">
                        <span class="stat-label">Total GL Records</span>
                        <span class="stat-value">${r.gl_count.toLocaleString()}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Max CONTEO</span>
                        <span class="stat-value">${r.max_conteo.toLocaleString()}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Pending Sync</span>
                        <span class="stat-value">${r.pending_count.toLocaleString()}</span>
                    </div>
                </div>`;
        }

        resultsDiv.innerHTML = html;
    } catch (err) {
        resultsDiv.innerHTML = `
            <div class="test-result-item error">
                <span class="test-icon">&#10007;</span>
                <div class="test-detail">
                    <div class="label">Test Failed</div>
                    <div class="message">${escapeHtml(err.message)}</div>
                </div>
            </div>`;
    }
}

// --- Modal Helpers ---

function openModal() {
    document.getElementById('modal-overlay').style.display = 'flex';
}

function closeModal() {
    document.getElementById('modal-overlay').style.display = 'none';
    editingId = null;
}

function closeTestModal() {
    document.getElementById('test-modal').style.display = 'none';
}

function clearForm() {
    document.getElementById('conn-id').value = '';
    document.getElementById('conn-name').value = '';
    document.getElementById('conn-enabled').checked = false;
    document.getElementById('fb-host').value = 'localhost';
    document.getElementById('fb-port').value = '3050';
    document.getElementById('fb-database').value = '';
    document.getElementById('fb-user').value = 'SYSDBA';
    document.getElementById('fb-password').value = 'masterkey';
    document.getElementById('sc-url').value = '';
    document.getElementById('sc-company').value = '';
    document.getElementById('sc-token').value = '';
    document.getElementById('sync-gl-interval').value = '15';
    document.getElementById('sync-ref-interval').value = '24';
    document.getElementById('sync-batch-size').value = '500';
}

// --- Utilities ---

function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}
