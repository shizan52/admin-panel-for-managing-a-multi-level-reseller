/**
 * Set key active/inactive (block/unblock) - super_seller only
 * @param {number} keyId - Key ID
 * @param {boolean} isActive - true to activate, false to block
 */
async function setKeyActiveStatus(keyId, isActive) {
    try {
        const response = await fetch(`/api/keys/set-active/${keyId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ is_active: isActive })
        });
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error setting key active status:', error);
        return { success: false, message: 'Network error' };
    }
}
// keys.js - Key Management functionality for all dashboards

/**
 * Load keys list
 */
async function loadKeys() {
    try {
        const response = await fetch('/api/keys/list');
        const data = await response.json();
        
        if (response.ok) {
            return data;
        } else {
            console.error('Failed to load keys:', data.message);
            return null;
        }
    } catch (error) {
        console.error('Error loading keys:', error);
        return null;
    }
}

/**
 * Create a new key
 * @param {string} name - Key name
 */
async function createKey(name) {
    try {
        const response = await fetch('/api/keys/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name })
        });
        
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error creating key:', error);
        return { success: false, message: 'Network error' };
    }
}

/**
 * Update paid status of a key
 * @param {number} keyId - Key ID
 * @param {boolean} isPaid - Paid status
 * @param {number} durationDays - Duration in days (7, 15, 30, 60, 90)
 * @param {boolean} extend - If true, extend existing validity; if false, replace it
 */
async function updatePaidStatus(keyId, isPaid, durationDays = 30, extend = false) {
    try {
        const response = await fetch(`/api/keys/update-paid/${keyId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ is_paid: isPaid, duration_days: durationDays, extend: extend })
        });
        
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error updating paid status:', error);
        return { success: false, message: 'Network error' };
    }
}

/**
 * Reset device (IP) for a key
 * @param {number} keyId - Key ID
 */
async function resetDevice(keyId) {
    try {
        const response = await fetch(`/api/keys/reset-device/${keyId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error resetting device:', error);
        return { success: false, message: 'Network error' };
    }
}

/**
 * Delete a key
 * @param {number} keyId - Key ID
 */
async function deleteKey(keyId) {
    try {
        const response = await fetch(`/api/keys/delete/${keyId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error deleting key:', error);
        return { success: false, message: 'Network error' };
    }
}

/**
 * Toggle block status for a key (block/unblock)
 * @param {number} keyId - Key ID
 */
async function toggleBlockKey(keyId) {
    try {
        const response = await fetch(`/api/keys/toggle-block/${keyId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error toggling block status:', error);
        return { success: false, message: 'Network error' };
    }
}

/**
 * Get access history for a key
 * @param {number} keyId - Key ID
 */
async function getKeyAccessHistory(keyId) {
    try {
        const response = await fetch(`/api/keys/access-history/${keyId}`);
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error loading access history:', error);
        return { success: false, message: 'Network error' };
    }
}

/**
 * Format date for display
 * @param {string} dateString - ISO date string
 */
function formatKeyDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    
    // Less than 1 minute
    if (diff < 60000) {
        return 'Just now';
    }
    
    // Less than 1 hour
    if (diff < 3600000) {
        const minutes = Math.floor(diff / 60000);
        return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
    }
    
    // Less than 24 hours
    if (diff < 86400000) {
        const hours = Math.floor(diff / 3600000);
        return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    }
    
    // Less than 7 days
    if (diff < 604800000) {
        const days = Math.floor(diff / 86400000);
        return `${days} day${days > 1 ? 's' : ''} ago`;
    }
    
    // Otherwise show full date
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

/**
 * Get role badge for display
 */
function getKeyRoleBadge(role) {
    const colors = {
        'admin': '#fb8c00',
        'super_seller': '#1de9b6',
        'seller': '#00bcd4'
    };
    const names = {
        'admin': 'Admin',
        'super_seller': 'Super Seller',
        'seller': 'Seller'
    };
    const color = colors[role] || '#888';
    const name = names[role] || role;
    
    return `<span style="background:${color};color:#fff;padding:4px 12px;border-radius:12px;font-size:0.85rem;font-weight:600;">${name}</span>`;
}

/**
 * Generate create key HTML
 */
function generateCreateKeyHTML() {
    return `
        <div style="max-width:700px;margin:40px auto 0 auto;padding:32px;background:#fff;border-radius:10px;box-shadow:0 2px 8px rgba(0,0,0,0.07);width:calc(100% - 40px);">
            <div style="margin-bottom:24px;">
                <h2 style="color:#d32f2f;margin:0;">🔑 Create New Key</h2>
                <p style="color:#888;margin:5px 0 0 0;font-size:0.95rem;">
                    Enter a unique name - this will be your Secret Key for software login
                </p>
            </div>
            
            <form id="createKeyForm">
                <div style="margin-bottom:20px;">
                    <label style="display:block;margin-bottom:6px;font-weight:600;color:#555;">Key Name (will be your Secret Key):</label>
                    <input 
                        type="text" 
                        id="keyName" 
                        required 
                        minlength="3"
                        placeholder="Enter a unique name (e.g., CUSTOMER001, MYKEY123)"
                        style="width:100%;padding:12px;border-radius:6px;border:1px solid #ccc;font-size:16px;box-sizing:border-box;"
                    />
                    <small style="color:#d32f2f;font-size:0.85rem;font-weight:600;">⚠️ Important: This name will be your Secret Key. Choose wisely - must be globally unique!</small>
                </div>
                
                <div style="display:flex;gap:12px;flex-wrap:wrap;">
                    <button 
                        type="submit" 
                        id="createKeyBtn"
                        style="flex:1;min-width:150px;background:#4CAF50;color:#fff;padding:12px 24px;border:none;border-radius:6px;font-size:16px;font-weight:600;cursor:pointer;transition:background 0.3s;"
                    >
                        Create Key
                    </button>
                    <button 
                        type="button" 
                        onclick="showContent('all-keys')"
                        style="flex:1;min-width:150px;background:#888;color:#fff;padding:12px 24px;border:none;border-radius:6px;font-size:16px;font-weight:600;cursor:pointer;transition:background 0.3s;"
                    >
                        Cancel
                    </button>
                </div>
            </form>
            
            <!-- Success message (hidden by default) -->
            <div id="keyCreatedSuccess" style="display:none;margin-top:24px;padding:20px;background:#e8f5e9;border-left:4px solid #4CAF50;border-radius:6px;">
                <h3 style="margin:0 0 12px 0;color:#2e7d32;">✅ Key Created Successfully!</h3>
                <div style="background:#fff;padding:16px;border-radius:6px;margin-bottom:12px;">
                    <div style="margin-bottom:8px;">
                        <strong>Your Secret Key:</strong>
                        <div style="font-size:24px;font-weight:bold;color:#d32f2f;font-family:monospace;margin-top:8px;letter-spacing:2px;" id="generatedKeyCode"></div>
                    </div>
                    <button 
                        onclick="copyKeyCode()"
                        style="background:#2196F3;color:#fff;padding:8px 16px;border:none;border-radius:4px;cursor:pointer;font-size:14px;"
                    >
                        📋 Copy Secret Key
                    </button>
                </div>
                <p class="copy-note" style="margin:0;color:#d32f2f;font-size:1rem;font-weight:600;display:block;">
                    ⚠️ <strong>Important:</strong> This is your Secret Key for software login. Share it with your customer securely!
                </p>
            </div>
        </div>
    `;
}

/**
 * Generate manage keys HTML (All Keys view)
 * Redesigned for super_seller_dashboard (screenshot style, static data)
 */
async function generateManageKeysHTML() {
    try {
        // Detect theme (default: light)
        let theme = window.dashboardTheme || 'light';
        // Fetch real keys from backend
        const data = await loadKeys();
        if (!data || !data.success) {
            return `<div style="text-align:center;padding:60px 20px;"><i class="fas fa-exclamation-triangle" style="font-size:2rem;color:#d32f2f;"></i><p style="margin-top:16px;color:#d32f2f;">Error loading keys.<br>${data && data.message ? data.message : 'Unknown error'}</p></div>`;
        }
        // Map backend keys to expected format for UI
        // Detect user role (from window.currentUserRole if set by backend template)
        let userRole = window.currentUserRole || '';
        let currentUserId = data.current_user_id || null;
        let currentRole = data.current_role || '';
        const keys = (data.keys || []).map(k => {
            // Compute status, paid, mac, days_left, expires_on for UI
            let status = 'Inactive';
            let paid = false;
            let expires_on = '-';
            let days_left = 0;
            if (k.active_until) {
                const today = new Date();
                const exp = new Date(k.active_until);
                days_left = Math.max(0, Math.ceil((exp - today) / (1000*60*60*24)));
                expires_on = k.active_until;
                if (k.is_active || days_left > 0) status = 'Active';
            }
            if (k.is_paid) paid = true;
            // MAC address: use k.mac or k.ip_address or 'unknown'
            let mac = k.mac || k.mac_address || k.ip_address || 'Not bound';
            // Always map key_code for Secret Key column
            let key_code = k.key_code || k.code || '-';
            return {
                id: k.id,
                name: k.name,
                key_code: key_code,
                created_at: k.created_at ? k.created_at.split('T')[0] : '-',
                expires_on,
                days_left,
                status,
                paid,
                mac,
                is_active: k.is_active,
                is_blocked: k.is_blocked || false,
                blocked: k.is_active === 0,
                is_paid: k.is_paid,
                created_by: k.created_by,
                seller_created_by: k.seller_created_by,
            };
        });

        // Card stats (static for now)
        const total = keys.length;
        const active = keys.filter(k => k.status === 'Active').length;
        const paid = keys.filter(k => k.paid).length;
        const filtered = total; // for demo

        // Theme colors
        let grad, accent, accentText, statBg, statText, tableHeadBg, tableHeadText, filterActiveBg, filterActiveText, cardText;
        if (theme === 'dark') {
            grad = 'linear-gradient(135deg,#232323 0%,#111 100%)'; // dark gray/black
            accent = '#d32f2f';
            accentText = '#fff';
            statBg = 'rgba(211,47,47,0.18)'; // subtle red for stat cards
            statText = '#fff';
            tableHeadBg = '#232323';
            tableHeadText = '#fff';
            filterActiveBg = '#d32f2f';
            filterActiveText = '#fff';
            cardText = '#fff';
        } else {
            grad = 'linear-gradient(135deg,#d32f2f 0%,#ff8a65 100%)';
            accent = '#d32f2f';
            accentText = '#fff';
            statBg = 'rgba(255,255,255,0.10)';
            statText = '#fff';
            tableHeadBg = '#d32f2f';
            tableHeadText = '#fff';
            filterActiveBg = '#d32f2f';
            filterActiveText = '#fff';
            cardText = '#fff';
        }
        let html = `
        <div style="background:${grad};padding:32px 0 0 0;min-height:100vh;">
            <div style="max-width:1200px;margin:0 auto;padding:0 24px;">
                <h2 style="color:${cardText};font-size:2.2rem;font-weight:700;margin-bottom:18px;">Active Keys Dashboard</h2>
                <p style="color:#ffeaea;font-size:1.1rem;margin-bottom:32px;">Manage and monitor all your license keys</p>

                <!-- Stat cards -->
                <div style="display:flex;gap:18px;flex-wrap:wrap;margin-bottom:28px;">
                    <div style="flex:1;min-width:180px;background:${statBg};border-radius:16px;padding:24px 0;text-align:center;color:${statText};backdrop-filter:blur(2px);">
                        <div style="font-size:2.1rem;font-weight:700;">${total}</div>
                        <div style="font-size:1.1rem;opacity:0.85;">Total Keys</div>
                    </div>
                    <div style="flex:1;min-width:180px;background:${statBg};border-radius:16px;padding:24px 0;text-align:center;color:${statText};backdrop-filter:blur(2px);">
                        <div style="font-size:2.1rem;font-weight:700;">${active}</div>
                        <div style="font-size:1.1rem;opacity:0.85;">Active</div>
                    </div>
                    <div style="flex:1;min-width:180px;background:${statBg};border-radius:16px;padding:24px 0;text-align:center;color:${statText};backdrop-filter:blur(2px);">
                        <div style="font-size:2.1rem;font-weight:700;">${paid}</div>
                        <div style="font-size:1.1rem;opacity:0.85;">Paid</div>
                    </div>
                </div>

                <!-- Search, filter, actions -->
                <div style="background:rgba(255,255,255,0.13);border-radius:12px;padding:18px 18px 10px 18px;box-shadow:0 2px 8px rgba(0,0,0,0.04);margin-bottom:18px;display:flex;flex-wrap:wrap;align-items:center;gap:12px;">
                    <input type="text" id="keySearchInput" placeholder="Search by key or MAC address..." style="flex:2;min-width:220px;padding:10px 16px;border-radius:8px;border:none;font-size:1.1rem;outline:none;" />
                    <div style="display:flex;gap:8px;flex-wrap:wrap;">
                        <button class="filter-btn" data-filter="all" style="background:#fff;color:${accent};border:none;padding:8px 18px;border-radius:8px;font-weight:600;cursor:pointer;">All</button>
                        <button class="filter-btn" data-filter="active" style="background:#fff;color:${accent};border:none;padding:8px 18px;border-radius:8px;font-weight:600;cursor:pointer;">Active</button>
                        <button class="filter-btn" data-filter="inactive" style="background:#fff;color:${accent};border:none;padding:8px 18px;border-radius:8px;font-weight:600;cursor:pointer;">Inactive</button>
                        <button class="filter-btn" data-filter="paid" style="background:#fff;color:${accent};border:none;padding:8px 18px;border-radius:8px;font-weight:600;cursor:pointer;">Paid</button>
                        <button class="filter-btn" data-filter="unpaid" style="background:#fff;color:${accent};border:none;padding:8px 18px;border-radius:8px;font-weight:600;cursor:pointer;">Unpaid</button>
                    </div>
                    <!-- Block Selected button removed for seller_dashboard -->
                    <button id="resetSelectedBtn" style="background:#43a047;color:#fff;border:none;padding:8px 18px;border-radius:8px;font-weight:600;cursor:pointer;">Reset Selected (0)</button>
                    <button id="refreshBtn" style="background:#fff;color:${accent};border:1px solid ${accent};padding:8px 18px;border-radius:8px;font-weight:600;cursor:pointer;float:right;">⟳ Refresh</button>
                </div>

                <!-- Table -->
                <div style="background:#fff;border-radius:14px;box-shadow:0 2px 8px rgba(0,0,0,0.07);padding:0 0 8px 0;overflow-x:auto;">
                    <table style="width:100%;border-collapse:collapse;min-width:900px;">
                        <thead>
                            <tr style="background:${tableHeadBg};color:${tableHeadText};">
                                <th style="padding:14px 8px;text-align:left;font-weight:700;font-size:1rem;"><input type="checkbox" id="selectAllKeys" /></th>
                                <th style="padding:14px 8px;text-align:left;font-weight:700;font-size:1rem;">Customer</th>
                                <th style="padding:14px 8px;text-align:left;font-weight:700;font-size:1rem;">Secret Key</th>
                                <th style="padding:14px 8px;text-align:left;font-weight:700;font-size:1rem;">CREATED</th>
                                <th style="padding:14px 8px;text-align:left;font-weight:700;font-size:1rem;">EXPIRES ON</th>
                                <th style="padding:14px 8px;text-align:left;font-weight:700;font-size:1rem;">STATUS</th>
                                <th style="padding:14px 8px;text-align:left;font-weight:700;font-size:1rem;">PAID</th>
                                <th style="padding:14px 8px;text-align:left;font-weight:700;font-size:1rem;">MAC ADDRESS</th>
                                <th style="padding:14px 8px;text-align:left;font-weight:700;font-size:1rem;">ACTIONS</th>
                            </tr>
                        </thead>
                        <tbody id="keysTableBody"></tbody>
                    </table>
                </div>
            </div>
        </div>
        <style>
            body { background: #f5f5f5; }
            .filter-btn.active { background: ${filterActiveBg} !important; color: ${filterActiveText} !important; }
        </style>
        `;
        // After rendering, attach JS events and render table
        setTimeout(() => {
            let filteredKeys = [...keys];
            let selectedKeys = [];
            const renderTable = () => {
                const tbody = document.getElementById('keysTableBody');
                if (!tbody) return;
                tbody.innerHTML = filteredKeys.map(key => {
                    let actionBtn = '';
                    
                    // Permission checks:
                    // 1. Seller can only reset their own keys (created_by === currentUserId)
                    // 2. Super_seller can only paid/block keys where seller's created_by === currentUserId
                    // 3. Admin/Master can block any key
                    
                    // Checkbox permission check
                    let canSelect = true;
                    let checkboxDisabled = '';
                    if (currentRole === 'seller' || userRole === 'seller') {
                        canSelect = key.created_by === currentUserId;
                        checkboxDisabled = canSelect ? '' : 'disabled';
                    }
                    
                    if (userRole === 'super_seller' || currentRole === 'super_seller') {
                        // Super seller: show Paid/Unpaid AND Block/Unblock ONLY for sellers they created
                        const canManage = key.seller_created_by === currentUserId;
                        
                        if (canManage) {
                            let paidBtn = '';
                            if (key.is_paid) {
                                paidBtn = `<button class="mark-unpaid-btn" data-key-id="${key.id}" style="background:#e53935;color:#fff;border:none;padding:6px 16px;border-radius:8px;font-weight:600;cursor:pointer;">Mark as Unpaid</button>`;
                            } else {
                                paidBtn = `<button class="mark-paid-btn" data-key-id="${key.id}" style="background:#43a047;color:#fff;border:none;padding:6px 16px;border-radius:8px;font-weight:600;cursor:pointer;">Mark as Paid</button>`;
                            }
                            let blockBtn = '';
                            if (key.is_active) {
                                blockBtn = `<button class="block-btn" data-key-id="${key.id}" style="background:#e53935;color:#fff;border:none;padding:6px 16px;border-radius:8px;font-weight:600;cursor:pointer;">Block</button>`;
                            } else {
                                blockBtn = `<button class="unblock-btn" data-key-id="${key.id}" style="background:#43a047;color:#fff;border:none;padding:6px 16px;border-radius:8px;font-weight:600;cursor:pointer;">Unblock</button>`;
                            }
                            actionBtn = paidBtn + ' ' + blockBtn;
                        } else {
                            // No permission for this key
                            actionBtn = `<span style="color:#999;font-style:italic;">No access</span>`;
                        }
                    } else if (userRole === 'admin' || userRole === 'master' || currentRole === 'admin' || currentRole === 'master') {
                        // Admin/Master: only Block/Unblock (no paid/unpaid controls)
                        if (key.is_active) {
                            actionBtn = `<button class="block-btn" data-key-id="${key.id}" style="background:#e53935;color:#fff;border:none;padding:6px 16px;border-radius:8px;font-weight:600;cursor:pointer;">Block</button>`;
                        } else {
                            actionBtn = `<button class="unblock-btn" data-key-id="${key.id}" style="background:#43a047;color:#fff;border:none;padding:6px 16px;border-radius:8px;font-weight:600;cursor:pointer;">Unblock</button>`;
                        }
                    } else {
                        // Seller: can reset, block/unblock, and delete their own keys
                        const isOwnKey = key.created_by === currentUserId;
                        if (isOwnKey) {
                            // Build action buttons for sellers
                            let resetBtn = `<button class="reset-device-btn" data-key-id="${key.id}" style="background:#2196F3;color:#fff;border:none;padding:6px 12px;border-radius:6px;font-weight:600;cursor:pointer;margin:2px;">🔄 Reset</button>`;
                            
                            let blockBtn = '';
                            const isBlocked = key.is_blocked || false;
                            if (isBlocked) {
                                blockBtn = `<button class="seller-unblock-btn" data-key-id="${key.id}" style="background:#43a047;color:#fff;border:none;padding:6px 12px;border-radius:6px;font-weight:600;cursor:pointer;margin:2px;">✅ Unblock</button>`;
                            } else {
                                blockBtn = `<button class="seller-block-btn" data-key-id="${key.id}" style="background:#ff9800;color:#fff;border:none;padding:6px 12px;border-radius:6px;font-weight:600;cursor:pointer;margin:2px;">🚫 Block</button>`;
                            }
                            
                            let deleteBtn = `<button class="seller-delete-btn" data-key-id="${key.id}" style="background:#e53935;color:#fff;border:none;padding:6px 12px;border-radius:6px;font-weight:600;cursor:pointer;margin:2px;">🗑️ Delete</button>`;
                            
                            actionBtn = `<div style="display:flex;flex-wrap:wrap;gap:4px;">${resetBtn}${blockBtn}${deleteBtn}</div>`;
                        } else {
                            actionBtn = `<span style="color:#999;font-style:italic;">No access</span>`;
                        }
                    }
                    return `
                    <tr>
                        <td style="padding:10px 8px;text-align:center;"><input type="checkbox" class="key-checkbox" data-key-id="${key.id}" ${selectedKeys.includes(key.id)?'checked':''} ${checkboxDisabled}/></td>
                        <td style="padding:10px 8px;font-weight:600;letter-spacing:1px;">${key.name}</td>
                        <td style="padding:10px 8px;font-family:monospace;">${key.key_code}</td>
                        <td style="padding:10px 8px;">${key.created_at}</td>
                        <td style="padding:10px 8px;"><div style="display:flex;align-items:center;gap:8px;"><span style="font-weight:700;">${key.days_left}D</span><span style="background:#e3f2fd;color:#1976d2;padding:2px 10px;border-radius:12px;font-size:0.95rem;">${key.expires_on}</span></div></td>
                        <td style="padding:10px 8px;">
                            <div style="display:flex;flex-direction:column;gap:4px;">
                                <span style="color:${key.status==='Active'?'#43a047':'#e53935'};font-weight:700;">${key.status}</span>
                                ${key.is_blocked ? '<span style="background:#ff9800;color:#fff;padding:2px 8px;border-radius:8px;font-size:0.8rem;font-weight:600;">🚫 BLOCKED</span>' : ''}
                            </div>
                        </td>
                        <td style="padding:10px 8px;"><span style="color:${key.paid?'#43a047':'#e53935'};font-weight:700;">${key.paid?'Paid':'Unpaid'}</span></td>
                        <td style="padding:10px 8px;font-family:monospace;">${key.mac}</td>
                        <td style="padding:10px 8px;">${actionBtn}</td>
                    </tr>
                    `;
                }).join('');
                const selectAll = document.getElementById('selectAllKeys');
                if (selectAll) selectAll.checked = selectedKeys.length === filteredKeys.length && filteredKeys.length > 0;
                // Block Selected button removed for seller_dashboard
                document.getElementById('resetSelectedBtn').textContent = `Reset Selected (${selectedKeys.length})`;
            };
            // Search
            const searchInput = document.getElementById('keySearchInput');
            if (searchInput) {
                searchInput.addEventListener('input', function() {
                    const val = this.value.toLowerCase();
                    filteredKeys = keys.filter(k => k.name.toLowerCase().includes(val) || k.mac.toLowerCase().includes(val));
                    selectedKeys = selectedKeys.filter(id => filteredKeys.some(k => k.id === id));
                    renderTable();
                });
            }
            // Filter
            document.querySelectorAll('.filter-btn').forEach(btn => {
                btn.addEventListener('click', function() {
                    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                    this.classList.add('active');
                    const f = this.getAttribute('data-filter');
                    if (f === 'all') filteredKeys = [...keys];
                    else if (f === 'active') filteredKeys = keys.filter(k => k.status === 'Active');
                    else if (f === 'inactive') filteredKeys = keys.filter(k => k.status !== 'Active');
                    else if (f === 'paid') filteredKeys = keys.filter(k => k.paid);
                    else if (f === 'unpaid') filteredKeys = keys.filter(k => !k.paid);
                    selectedKeys = selectedKeys.filter(id => filteredKeys.some(k => k.id === id));
                    renderTable();
                });
            });
            // Select all
            const selectAll = document.getElementById('selectAllKeys');
            if (selectAll) {
                selectAll.addEventListener('change', function() {
                    if (this.checked) {
                        // For sellers, only select keys they created
                        if (currentRole === 'seller' || userRole === 'seller') {
                            selectedKeys = filteredKeys.filter(k => k.created_by === currentUserId).map(k => k.id);
                        } else {
                            selectedKeys = filteredKeys.map(k => k.id);
                        }
                    } else {
                        selectedKeys = [];
                    }
                    renderTable();
                });
            }
            // Row checkbox
            const tbody = document.getElementById('keysTableBody');
            if (tbody) {
                tbody.addEventListener('change', function(e) {
                    if (e.target.classList.contains('key-checkbox')) {
                        const id = parseInt(e.target.getAttribute('data-key-id'));
                        
                        // For sellers, check if they own this key
                        if (currentRole === 'seller' || userRole === 'seller') {
                            const key = filteredKeys.find(k => k.id === id);
                            if (key && key.created_by !== currentUserId) {
                                e.target.checked = false;
                                alert('You can only select keys that you created');
                                return;
                            }
                        }
                        
                        if (e.target.checked) { if (!selectedKeys.includes(id)) selectedKeys.push(id); }
                        else { selectedKeys = selectedKeys.filter(x => x !== id); }
                        renderTable();
                    }
                });
                tbody.addEventListener('click', async function(e) {
                    // Reset device button (all roles with permission)
                    if (e.target.classList.contains('reset-btn') || e.target.classList.contains('reset-device-btn')) {
                        const keyId = parseInt(e.target.getAttribute('data-key-id'));
                        if (!keyId) return;
                        if (!confirm('Are you sure you want to reset device binding for this key? This will allow login from a new device.')) return;
                        try {
                            const res = await resetDevice(keyId);
                            if (res && res.success) {
                                alert(res.message || 'Device reset successfully');
                                showContent('all-keys');
                            } else {
                                alert('Error resetting device: ' + (res && res.message ? res.message : 'Unknown error'));
                            }
                        } catch (err) {
                            console.error('Reset device error:', err);
                            alert('Network error while resetting device');
                        }
                    }
                    
                    // Seller-specific block button
                    if (e.target.classList.contains('seller-block-btn')) {
                        const keyId = parseInt(e.target.getAttribute('data-key-id'));
                        if (!confirm('⚠️ Block this key? Users will NOT be able to login with this key until you unblock it.')) return;
                        try {
                            const result = await toggleBlockKey(keyId);
                            if (result.success) {
                                alert('✅ Key blocked successfully! Software login is now disabled for this key.');
                                showContent('all-keys');
                            } else {
                                alert('❌ Error: ' + result.message);
                            }
                        } catch (err) {
                            console.error('Block key error:', err);
                            alert('Network error while blocking key');
                        }
                    }
                    
                    // Seller-specific unblock button
                    if (e.target.classList.contains('seller-unblock-btn')) {
                        const keyId = parseInt(e.target.getAttribute('data-key-id'));
                        if (!confirm('Unblock this key? Users will be able to login with this key again.')) return;
                        try {
                            const result = await toggleBlockKey(keyId);
                            if (result.success) {
                                alert('✅ Key unblocked successfully! Software login is now enabled.');
                                showContent('all-keys');
                            } else {
                                alert('❌ Error: ' + result.message);
                            }
                        } catch (err) {
                            console.error('Unblock key error:', err);
                            alert('Network error while unblocking key');
                        }
                    }
                    
                    // Seller-specific delete button
                    if (e.target.classList.contains('seller-delete-btn')) {
                        const keyId = parseInt(e.target.getAttribute('data-key-id'));
                        if (!confirm('⚠️⚠️ PERMANENTLY DELETE this key? This action CANNOT be undone! The key will be completely removed and unusable.')) return;
                        try {
                            const result = await deleteKey(keyId);
                            if (result.success) {
                                alert('✅ Key deleted successfully!');
                                showContent('all-keys');
                            } else {
                                alert('❌ Error: ' + result.message);
                            }
                        } catch (err) {
                            console.error('Delete key error:', err);
                            alert('Network error while deleting key');
                        }
                    }
                    
                    // Super seller/Admin block button
                    if (e.target.classList.contains('block-btn')) {
                        const keyId = parseInt(e.target.getAttribute('data-key-id'));
                        if (confirm('Are you sure you want to block (deactivate) this key?')) {
                            const result = await setKeyActiveStatus(keyId, false);
                            if (result.success) {
                                alert('Key blocked (inactive) successfully!');
                                showContent('all-keys');
                            } else {
                                alert('Error: ' + result.message);
                            }
                        }
                    }
                    
                    // Super seller/Admin unblock button
                    if (e.target.classList.contains('unblock-btn')) {
                        const keyId = parseInt(e.target.getAttribute('data-key-id'));
                        if (confirm('Are you sure you want to unblock (activate) this key?')) {
                            const result = await setKeyActiveStatus(keyId, true);
                            if (result.success) {
                                alert('Key activated successfully!');
                                showContent('all-keys');
                            } else {
                                alert('Error: ' + result.message);
                            }
                        }
                    }
                    
                    if (e.target.classList.contains('mark-paid-btn')) {
                        const keyId = parseInt(e.target.getAttribute('data-key-id'));
                        if (confirm('Mark this key as PAID (activate for 30 days)?')) {
                            const result = await updatePaidStatus(keyId, true, 30, false);
                            if (result.success) {
                                alert('Key marked as PAID and activated for 30 days!');
                                showContent('all-keys');
                            } else {
                                alert('Error: ' + result.message);
                            }
                        }
                    }
                    if (e.target.classList.contains('mark-unpaid-btn')) {
                        const keyId = parseInt(e.target.getAttribute('data-key-id'));
                        if (confirm('Mark this key as UNPAID (deactivate)?')) {
                            const result = await updatePaidStatus(keyId, false, 30, false);
                            if (result.success) {
                                alert('Key marked as UNPAID and deactivated!');
                                showContent('all-keys');
                            } else {
                                alert('Error: ' + result.message);
                            }
                        }
                    }
                });
            }
            // Bulk actions
            // Block Selected button removed for seller_dashboard
            const resetBtn = document.getElementById('resetSelectedBtn');
            if (resetBtn) resetBtn.addEventListener('click', async function() {
                if (!selectedKeys || selectedKeys.length === 0) {
                    alert('No keys selected to reset');
                    return;
                }
                // For sellers: only reset keys they created (permission check)
                let keysToReset = selectedKeys;
                if (currentRole === 'seller' || userRole === 'seller') {
                    keysToReset = selectedKeys.filter(id => {
                        const key = filteredKeys.find(k => k.id === id);
                        return key && key.created_by === currentUserId;
                    });
                    if (keysToReset.length === 0) {
                        alert('You can only reset keys that you created');
                        return;
                    }
                    if (keysToReset.length < selectedKeys.length) {
                        if (!confirm(`You can only reset ${keysToReset.length} of ${selectedKeys.length} selected keys. Continue?`)) return;
                    }
                }
                if (!confirm('Reset device binding for selected keys?')) return;
                // Perform resets in parallel and collect results
                try {
                    const promises = keysToReset.map(id => resetDevice(id));
                    const results = await Promise.all(promises);
                    const failed = results.filter(r => !r || !r.success);
                    if (failed.length === 0) {
                        alert('Device reset for selected keys succeeded');
                    } else {
                        alert(`Some resets failed: ${failed.length} of ${results.length}`);
                    }
                    showContent('all-keys');
                } catch (err) {
                    console.error('Bulk reset error:', err);
                    alert('Network error while resetting selected keys');
                }
            });
            const exportBtn = document.getElementById('exportBtn');
            if (exportBtn) exportBtn.addEventListener('click', function() {
                alert('Export all (not implemented)');
            });
            const refreshBtn = document.getElementById('refreshBtn');
            if (refreshBtn) refreshBtn.addEventListener('click', function() {
                try {
                    // Reload the All Keys view and stay on the same page
                    if (typeof showContent === 'function') {
                        showContent('all-keys');
                    } else {
                        // Fallback: reload the page
                        window.location.reload();
                    }
                } catch (err) {
                    console.error('Refresh error:', err);
                    window.location.reload();
                }
            });
            // Initial render
            renderTable();
        }, 10);
        return html;
    } catch (err) {
        console.error('Error rendering All Keys dashboard:', err);
        return `<div style="text-align:center;padding:60px 20px;"><i class="fas fa-exclamation-triangle" style="font-size:2rem;color:#d32f2f;"></i><p style="margin-top:16px;color:#d32f2f;">Error loading keys dashboard.<br>${err.message || err}</p></div>`;
    }
}

/**
 * Initialize key management functionality
 * Call this after loading key management HTML
 */
function initKeyManagement() {
    // Create key form handler
    const createForm = document.getElementById('createKeyForm');
    if (createForm) {
        createForm.addEventListener('submit', async function(event) {
            event.preventDefault();
            const name = document.getElementById('keyName').value.trim();
            const submitBtn = document.getElementById('createKeyBtn');
            // Disable button and show loading
            submitBtn.disabled = true;
            submitBtn.textContent = 'Creating...';
            try {
                const result = await createKey(name);
                if (result.success) {
                    // Hide form
                    createForm.style.display = 'none';
                    // Show success message with key code
                    const successDiv = document.getElementById('keyCreatedSuccess');
                    const keyCodeDiv = document.getElementById('generatedKeyCode');
                    // Support both {key: {key_code: ...}} and {key_code: ...}
                    let code = (result.key && result.key.key_code) ? result.key.key_code : result.key_code;
                    keyCodeDiv.textContent = code;
                    successDiv.style.display = 'block';
                    // Store key code for copy function
                    window.currentKeyCode = code;
                    // Show note to user to copy and save
                    const note = successDiv.querySelector('.copy-note');
                    if (note) note.style.display = 'block';
                } else {
                    alert('Error: ' + result.message);
                    submitBtn.disabled = false;
                    submitBtn.textContent = 'Create Key';
                }
            } catch (error) {
                alert('Failed to create key. Please try again.');
                submitBtn.disabled = false;
                submitBtn.textContent = 'Create Key';
            }
        });
    }
    
    // Toggle paid status buttons
    const togglePaidBtns = document.querySelectorAll('.toggle-paid-btn');
    togglePaidBtns.forEach(btn => {
        btn.addEventListener('click', async function() {
            const keyId = parseInt(this.dataset.keyId);
            
            if (!confirm('Deactivate this key and remove active duration?')) return;
            
            this.disabled = true;
            this.textContent = 'Processing...';
            
            const result = await updatePaidStatus(keyId, false);
            
            if (result.success) {
                alert(result.message);
                showContent('all-keys');
            } else {
                alert('Error: ' + result.message);
                this.disabled = false;
                this.textContent = '❌ Unpay';
            }
        });
    });
    
    // Extend validity buttons
    const extendValidityBtns = document.querySelectorAll('.extend-validity-btn');
    extendValidityBtns.forEach(btn => {
        btn.addEventListener('click', async function() {
            const keyId = parseInt(this.dataset.keyId);
            const durationSelector = document.querySelector(`.extend-duration-selector[data-key-id="${keyId}"]`);
            const duration = parseInt(durationSelector.value);
            
            if (!confirm(`Extend this key's validity by ${duration} more days?`)) return;
            
            this.disabled = true;
            this.textContent = 'Extending...';
            
            const result = await updatePaidStatus(keyId, true, duration, true); // extend=true
            
            if (result.success) {
                alert(result.message);
                showContent('all-keys');
            } else {
                alert('Error: ' + result.message);
                this.disabled = false;
                this.textContent = '➕ Extend';
            }
        });
    });
    
    // Activate key buttons
    const activateKeyBtns = document.querySelectorAll('.activate-key-btn');
    activateKeyBtns.forEach(btn => {
        btn.addEventListener('click', async function() {
            const keyId = parseInt(this.dataset.keyId);
            const durationSelector = document.querySelector(`.duration-selector[data-key-id="${keyId}"]`);
            const durationDays = parseInt(durationSelector.value);
            
            if (!confirm(`Activate this key for ${durationDays} days?`)) return;
            
            this.disabled = true;
            this.textContent = 'Activating...';
            
            const result = await updatePaidStatus(keyId, true, durationDays);
            
            if (result.success) {
                alert(result.message);
                showContent('all-keys');
            } else {
                alert('Error: ' + result.message);
                this.disabled = false;
                this.textContent = '✅ Activate';
            }
        });
    });
    
    // Reset device buttons
    const resetDeviceBtns = document.querySelectorAll('.reset-device-btn');
    resetDeviceBtns.forEach(btn => {
        btn.addEventListener('click', async function() {
            const keyId = parseInt(this.dataset.keyId);
            
            if (!confirm('Reset device for this key? This will allow login from a new device/IP address.')) return;
            
            this.disabled = true;
            this.textContent = 'Resetting...';
            
            const result = await resetDevice(keyId);
            
            if (result.success) {
                alert(result.message);
                showContent('all-keys');
            } else {
                alert('Error: ' + result.message);
                this.disabled = false;
                this.textContent = '🔄 Reset Device';
            }
        });
    });
    
    // Delete key buttons
    const deleteKeyBtns = document.querySelectorAll('.delete-key-btn');
    deleteKeyBtns.forEach(btn => {
        btn.addEventListener('click', async function() {
            const keyId = parseInt(this.dataset.keyId);
            
            if (!confirm('⚠️ Are you sure you want to delete this key? This action cannot be undone!')) return;
            
            this.disabled = true;
            this.textContent = 'Deleting...';
            
            const result = await deleteKey(keyId);
            
            if (result.success) {
                alert(result.message);
                // Remove row from table
                const row = this.closest('tr');
                row.remove();
                
                // Check if table is empty
                const tbody = document.querySelector('tbody');
                if (tbody && tbody.children.length === 0) {
                    showContent('all-keys');
                }
            } else {
                alert('Error: ' + result.message);
                this.disabled = false;
                this.textContent = '🗑️ Delete';
            }
        });
    });
    
    // Toggle history buttons
    const toggleHistoryBtns = document.querySelectorAll('.toggle-history-btn');
    toggleHistoryBtns.forEach(btn => {
        btn.addEventListener('click', async function() {
            const keyId = parseInt(this.dataset.keyId);
            const historyRow = document.querySelector(`.history-row[data-key-id="${keyId}"]`);
            
            if (historyRow.style.display === 'none') {
                // Expand history
                this.textContent = '▼';
                historyRow.style.display = '';
                
                // Auto-load history on first expand
                const historyContent = historyRow.querySelector('.history-content');
                if (historyContent.innerHTML.includes('Click')) {
                    await loadAccessHistory(keyId);
                }
            } else {
                // Collapse history
                this.textContent = '▶';
                historyRow.style.display = 'none';
            }
        });
    });
    
    // Refresh history buttons
    const refreshHistoryBtns = document.querySelectorAll('.refresh-history-btn');
    refreshHistoryBtns.forEach(btn => {
        btn.addEventListener('click', async function() {
            const keyId = parseInt(this.dataset.keyId);
            await loadAccessHistory(keyId);
        });
    });
}

/**
 * Load and display access history for a key
 * @param {number} keyId - Key ID
 * @param {number} page - Page number (1-indexed)
 */
async function loadAccessHistory(keyId, page = 1) {
    const historyContent = document.querySelector(`.history-content[data-key-id="${keyId}"]`);
    if (!historyContent) return;
    
    // Show loading
    historyContent.innerHTML = '<p style="color:#888;text-align:center;padding:20px;">Loading history...</p>';
    
    const result = await getKeyAccessHistory(keyId);
    
    if (!result.success) {
        historyContent.innerHTML = `<p style="color:#d32f2f;text-align:center;padding:20px;">❌ ${result.message}</p>`;
        return;
    }
    
    const history = result.history || [];
    
    if (history.length === 0) {
        historyContent.innerHTML = '<p style="color:#888;text-align:center;padding:20px;">No access history found</p>';
        return;
    }
    
    // Pagination settings
    const itemsPerPage = 20;
    const totalPages = Math.ceil(history.length / itemsPerPage);
    const startIndex = (page - 1) * itemsPerPage;
    const endIndex = Math.min(startIndex + itemsPerPage, history.length);
    const paginatedHistory = history.slice(startIndex, endIndex);
    
    // Build history table
    let html = `
        <div style="overflow-x:auto;">
            <table style="width:100%;border-collapse:collapse;font-size:0.9rem;">
                <thead>
                    <tr style="background:#e3f2fd;border-bottom:2px solid #2196F3;">
                        <th style="padding:8px;text-align:left;font-weight:600;color:#555;">Date & Time</th>
                        <th style="padding:8px;text-align:left;font-weight:600;color:#555;">IP Address</th>
                        <th style="padding:8px;text-align:left;font-weight:600;color:#555;">User Agent</th>
                        <th style="padding:8px;text-align:left;font-weight:600;color:#555;">Status</th>
                        <th style="padding:8px;text-align:left;font-weight:600;color:#555;">Message</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    paginatedHistory.forEach(entry => {
        const statusColors = {
            'SUCCESS': '#4CAF50',
            'FAILED': '#f44336',
            'BLOCKED': '#ff9800'
        };
        const statusColor = statusColors[entry.status] || '#888';
        
        html += `
            <tr style="border-bottom:1px solid #ddd;">
                <td style="padding:8px;color:#555;">${formatKeyDate(entry.accessed_at)}</td>
                <td style="padding:8px;font-family:monospace;color:#2196F3;font-weight:600;">${entry.ip_address || 'N/A'}</td>
                <td style="padding:8px;color:#666;font-size:0.85rem;max-width:300px;overflow:hidden;text-overflow:ellipsis;" title="${entry.user_agent}">${entry.user_agent}</td>
                <td style="padding:8px;">
                    <span style="background:${statusColor};color:#fff;padding:3px 10px;border-radius:10px;font-size:0.8rem;font-weight:600;">
                        ${entry.status}
                    </span>
                </td>
                <td style="padding:8px;color:#666;">${entry.message}</td>
            </tr>
        `;
    });
    
    html += `
                </tbody>
            </table>
        </div>
    `;
    
    // Add pagination controls if needed
    if (totalPages > 1) {
        html += `
            <div style="display:flex;justify-content:space-between;align-items:center;margin-top:16px;padding:12px;background:#f5f5f5;border-radius:4px;">
                <div style="color:#666;font-size:0.9rem;">
                    Showing ${startIndex + 1}-${endIndex} of ${history.length} records
                </div>
                <div style="display:flex;gap:8px;">
                    <button 
                        onclick="loadAccessHistory(${keyId}, ${page - 1})"
                        ${page === 1 ? 'disabled' : ''}
                        style="padding:6px 12px;border:1px solid #ccc;border-radius:4px;background:${page === 1 ? '#f5f5f5' : '#fff'};cursor:${page === 1 ? 'not-allowed' : 'pointer'};font-size:0.85rem;"
                    >
                        ◀ Previous
                    </button>
                    <span style="padding:6px 12px;color:#666;font-size:0.85rem;">
                        Page ${page} of ${totalPages}
                    </span>
                    <button 
                        onclick="loadAccessHistory(${keyId}, ${page + 1})"
                        ${page === totalPages ? 'disabled' : ''}
                        style="padding:6px 12px;border:1px solid #ccc;border-radius:4px;background:${page === totalPages ? '#f5f5f5' : '#fff'};cursor:${page === totalPages ? 'not-allowed' : 'pointer'};font-size:0.85rem;"
                    >
                        Next ▶
                    </button>
                </div>
            </div>
        `;
    } else {
        html += `
            <p style="color:#888;font-size:0.85rem;margin-top:12px;text-align:right;">
                Showing all ${history.length} access attempt${history.length !== 1 ? 's' : ''}
            </p>
        `;
    }
    
    historyContent.innerHTML = html;
}

/**
 * Copy key code to clipboard
 */
function copyKeyCode() {
    if (window.currentKeyCode) {
        navigator.clipboard.writeText(window.currentKeyCode).then(() => {
            alert('✅ Key code copied to clipboard!');
        }).catch(() => {
            // Fallback for older browsers
            const temp = document.createElement('textarea');
            temp.value = window.currentKeyCode;
            document.body.appendChild(temp);
            temp.select();
            document.execCommand('copy');
            document.body.removeChild(temp);
            alert('✅ Key code copied to clipboard!');
        });
    }
}

/**
 * Filter keys table by search and status
 */
function filterKeys() {
    const searchInput = document.getElementById('searchKeysInput');
    const statusSelect = document.getElementById('filterStatusSelect');
    
    if (!searchInput || !statusSelect) return;
    
    const searchTerm = searchInput.value.toLowerCase().trim();
    const statusFilter = statusSelect.value;
    
    const rows = document.querySelectorAll('.key-row');
    let visibleCount = 0;
    
    rows.forEach(row => {
        const keyName = row.dataset.keyName;
        const keyCode = row.dataset.keyCode;
        const keyStatus = row.dataset.keyStatus;
        const keyIp = row.dataset.keyIp || '';
        
        // Check search match (name, code, OR IP)
        const searchMatch = searchTerm === '' || 
            keyName.includes(searchTerm) || 
            keyCode.includes(searchTerm) ||
            keyIp.toLowerCase().includes(searchTerm);
        
        // Check status match
        const statusMatch = statusFilter === 'all' || keyStatus === statusFilter;
        
        // Show/hide row AND its history row
        const historyRow = document.querySelector(`.history-row[data-key-id="${row.dataset.keyId}"]`);
        
        if (searchMatch && statusMatch) {
            row.style.display = '';
            if (historyRow) historyRow.style.display = historyRow.style.display === 'none' ? 'none' : '';
            visibleCount++;
        } else {
            row.style.display = 'none';
            if (historyRow) historyRow.style.display = 'none';
        }
    });
    
    // Update count display
    const countDisplay = document.getElementById('keysCountDisplay');
    if (countDisplay) {
        countDisplay.textContent = visibleCount;
    }
}
