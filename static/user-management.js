// user-management.js - User Management functionality for dashboards

/**
 * Get list of managed users
 */
async function getManagedUsers() {
    try {
        const response = await fetch('/api/users/list-managed');
        const data = await response.json();
        
        if (!data.success) {
            console.error('Failed to load users:', data.message);
            return null;
        }
        
        return data;
    } catch (error) {
        console.error('Error loading users:', error);
        return null;
    }
}

/**
 * Create a new user
 * @param {string} username - Username
 * @param {string} password - Password
 * @param {string} role - User role
 */
async function createUser(username, password, role) {
    try {
        const response = await fetch('/api/users/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: username,
                password: password,
                role: role
            })
        });
        
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error creating user:', error);
        return { success: false, message: 'Connection error' };
    }
}

/**
 * Delete a user
 * @param {number} userId - User ID
 */
async function deleteUser(userId) {
    try {
        const response = await fetch(`/api/users/delete/${userId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error deleting user:', error);
        return { success: false, message: 'Connection error' };
    }
}

/**
 * Update user password
 * @param {number} userId - User ID
 * @param {string} newPassword - New password
 */
async function updateUserPassword(userId, newPassword) {
    try {
        const response = await fetch(`/api/users/update-password/${userId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                password: newPassword
            })
        });
        
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error updating password:', error);
        return { success: false, message: 'Connection error' };
    }
}

/**
 * Get user statistics
 */
async function getUserStats() {
    try {
        const response = await fetch('/api/users/stats');
        const data = await response.json();
        
        if (!data.success) {
            console.error('Failed to load stats:', data.message);
            return null;
        }
        
        return data.stats;
    } catch (error) {
        console.error('Error loading stats:', error);
        return null;
    }
}

/**
 * Format date for display
 * @param {string} dateString - ISO date string
 */
function formatUserDate(dateString) {
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
 * Get role display name
 */
function getRoleDisplayName(role) {
    const roleNames = {
        'admin': 'Admin',
        'super_seller': 'Super Seller',
        'seller': 'Seller'
    };
    return roleNames[role] || role;
}

/**
 * Get role badge color
 */
function getRoleBadge(role) {
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
 * Generate user management HTML
 * @param {string} manageRole - Role being managed (admin/super_seller/seller)
 */
async function generateUserManagementHTML(manageRole) {
    const usersData = await getManagedUsers();
    const stats = await getUserStats();
    
    if (!usersData) {
        return `
            <div style="max-width:800px;margin:40px auto 0 auto;padding:32px;background:#fff;border-radius:10px;box-shadow:0 2px 8px rgba(0,0,0,0.07);text-align:center;width:calc(100% - 40px);">
                <h2 style="margin-bottom:24px;color:#d32f2f;">User Management</h2>
                <div style="color:#888;font-size:1.15rem;padding:32px 0;">Error loading users. Please try again.</div>
            </div>
        `;
    }
    
    const usersList = usersData.users || [];
    const managedRoles = usersData.managed_roles || [];
    const totalCount = stats ? stats.total : 0;
    
    // Get role name for display
    const roleDisplayName = getRoleDisplayName(manageRole);
    
    // Build HTML
    let html = `
        <div style="max-width:1000px;margin:40px auto 0 auto;padding:32px;background:#fff;border-radius:10px;box-shadow:0 2px 8px rgba(0,0,0,0.07);width:calc(100% - 40px);">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:24px;flex-wrap:wrap;gap:16px;">
                <div>
                    <h2 style="color:#d32f2f;margin:0;">👥 Manage ${roleDisplayName}s</h2>
                    <p style="color:#888;margin:5px 0 0 0;font-size:0.95rem;">
                        ${totalCount} total user${totalCount !== 1 ? 's' : ''}
                    </p>
                </div>
                <button id="createUserBtn" style="padding:10px 20px;background:#4CAF50;color:#fff;border:none;border-radius:8px;cursor:pointer;font-weight:bold;transition:all 0.3s;font-size:0.95rem;">
                    <i class="fas fa-plus-circle" style="margin-right:8px;"></i>Create ${roleDisplayName}
                </button>
            </div>
            
            <!-- Create User Form (Hidden by default) -->
            <div id="createUserForm" style="display:none;background:#f5f5f5;padding:20px;border-radius:8px;margin-bottom:24px;">
                <h3 style="margin-top:0;color:#333;">Create New ${roleDisplayName} Account</h3>
                <form id="userCreateForm">
                    <div style="margin-bottom:16px;">
                        <label style="display:block;margin-bottom:6px;font-weight:600;color:#555;">Username:</label>
                        <input type="text" id="newUsername" required minlength="3" style="width:calc(100% - 22px);padding:10px;border-radius:6px;border:1px solid #ccc;font-size:16px;" placeholder="Enter username (min 3 characters)">
                    </div>
                    <div style="margin-bottom:16px;">
                        <label style="display:block;margin-bottom:6px;font-weight:600;color:#555;">Password:</label>
                        <input type="password" id="newPassword" required minlength="6" style="width:calc(100% - 22px);padding:10px;border-radius:6px;border:1px solid #ccc;font-size:16px;" placeholder="Enter password (min 6 characters)">
                    </div>
                    <div style="margin-bottom:16px;">
                        <label style="display:block;margin-bottom:6px;font-weight:600;color:#555;">Confirm Password:</label>
                        <input type="password" id="confirmPassword" required minlength="6" style="width:calc(100% - 22px);padding:10px;border-radius:6px;border:1px solid #ccc;font-size:16px;" placeholder="Confirm password">
                    </div>
                    <input type="hidden" id="userRole" value="${manageRole}">
                    <div style="display:flex;gap:12px;">
                        <button type="submit" style="padding:10px 20px;background:#4CAF50;color:#fff;border:none;border-radius:6px;cursor:pointer;font-weight:bold;transition:all 0.3s;">Create Account</button>
                        <button type="button" id="cancelCreateBtn" style="padding:10px 20px;background:#888;color:#fff;border:none;border-radius:6px;cursor:pointer;font-weight:bold;transition:all 0.3s;">Cancel</button>
                    </div>
                </form>
            </div>
            
            <!-- Users List -->
            <div id="usersList">
    `;
    
    if (usersList.length === 0) {
        html += `
                <div style="text-align:center;padding:60px 20px;background:#f9f9f9;border-radius:8px;">
                    <i class="fas fa-users" style="font-size:3rem;color:#ccc;margin-bottom:16px;"></i>
                    <p style="color:#888;font-size:1.15rem;margin:0;">No ${roleDisplayName.toLowerCase()}s found</p>
                    <p style="color:#aaa;font-size:0.95rem;margin-top:8px;">Click "Create ${roleDisplayName}" to add a new user</p>
                </div>
        `;
    } else {
        html += `
                <div style="overflow-x:auto;">
                    <table style="width:100%;border-collapse:collapse;background:#fff;">
                        <thead>
                            <tr style="background:#f5f5f5;border-bottom:2px solid #ddd;">
                                <th style="padding:12px;text-align:left;font-weight:600;color:#555;">Username</th>
                                <th style="padding:12px;text-align:left;font-weight:600;color:#555;">Role</th>
                                <th style="padding:12px;text-align:left;font-weight:600;color:#555;">Created</th>
                                <th style="padding:12px;text-align:center;font-weight:600;color:#555;">Actions</th>
                            </tr>
                        </thead>
                        <tbody>
        `;
        
        usersList.forEach(user => {
            html += `
                            <tr style="border-bottom:1px solid #eee;" data-user-id="${user.id}">
                                <td style="padding:12px;">
                                    <div style="display:flex;align-items:center;gap:10px;">
                                        <i class="fas fa-user-circle" style="font-size:1.5rem;color:#888;"></i>
                                        <span style="font-weight:600;color:#333;">${user.username}</span>
                                    </div>
                                </td>
                                <td style="padding:12px;">${getRoleBadge(user.role)}</td>
                                <td style="padding:12px;color:#666;font-size:0.9rem;">${formatUserDate(user.created_at)}</td>
                                <td style="padding:12px;text-align:center;">
                                    <button class="resetPasswordBtn" data-user-id="${user.id}" data-username="${user.username}" style="padding:6px 12px;background:#fb8c00;color:#fff;border:none;border-radius:4px;cursor:pointer;margin-right:8px;font-size:0.85rem;transition:all 0.3s;" title="Reset Password">
                                        <i class="fas fa-key"></i> Reset
                                    </button>
                                    <button class="deleteUserBtn" data-user-id="${user.id}" data-username="${user.username}" style="padding:6px 12px;background:#d32f2f;color:#fff;border:none;border-radius:4px;cursor:pointer;font-size:0.85rem;transition:all 0.3s;" title="Delete User">
                                        <i class="fas fa-trash"></i> Delete
                                    </button>
                                </td>
                            </tr>
            `;
        });
        
        html += `
                        </tbody>
                    </table>
                </div>
        `;
    }
    
    html += `
            </div>
        </div>
    `;
    
    return html;
}

/**
 * Initialize user management functionality
 * Call this after loading user management HTML
 */
function initUserManagement() {
    const createUserBtn = document.getElementById('createUserBtn');
    const createUserForm = document.getElementById('createUserForm');
    const cancelCreateBtn = document.getElementById('cancelCreateBtn');
    const userCreateForm = document.getElementById('userCreateForm');
    
    // Toggle create form
    if (createUserBtn) {
        createUserBtn.addEventListener('click', function() {
            createUserForm.style.display = 'block';
            createUserBtn.style.display = 'none';
            // Scroll to form
            createUserForm.scrollIntoView({ behavior: 'smooth', block: 'start' });
        });
    }
    
    // Cancel create
    if (cancelCreateBtn) {
        cancelCreateBtn.addEventListener('click', function() {
            createUserForm.style.display = 'none';
            createUserBtn.style.display = 'inline-block';
            userCreateForm.reset();
        });
    }
    
    // Handle create user form submission
    if (userCreateForm) {
        userCreateForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const username = document.getElementById('newUsername').value.trim();
            const password = document.getElementById('newPassword').value.trim();
            const confirmPassword = document.getElementById('confirmPassword').value.trim();
            const role = document.getElementById('userRole').value;
            
            // Validate passwords match
            if (password !== confirmPassword) {
                alert('Passwords do not match!');
                return;
            }
            
            // Disable submit button
            const submitBtn = userCreateForm.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            submitBtn.textContent = 'Creating...';
            
            // Create user
            const result = await createUser(username, password, role);
            
            if (result.success) {
                alert(result.message || 'User created successfully!');
                // Reload page to show new user
                location.reload();
            } else {
                alert('Error: ' + (result.message || 'Failed to create user'));
                submitBtn.disabled = false;
                submitBtn.textContent = 'Create Account';
            }
        });
    }
    
    // Handle delete buttons
    const deleteButtons = document.querySelectorAll('.deleteUserBtn');
    deleteButtons.forEach(btn => {
        btn.addEventListener('click', async function() {
            const userId = this.getAttribute('data-user-id');
            const username = this.getAttribute('data-username');
            
            if (!confirm(`Are you sure you want to delete user "${username}"? This action cannot be undone.`)) {
                return;
            }
            
            // Disable button
            this.disabled = true;
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Deleting...';
            
            // Delete user
            const result = await deleteUser(userId);
            
            if (result.success) {
                alert(result.message || 'User deleted successfully!');
                // Remove row from table
                const row = document.querySelector(`tr[data-user-id="${userId}"]`);
                if (row) {
                    row.remove();
                }
                // Reload to update count
                location.reload();
            } else {
                alert('Error: ' + (result.message || 'Failed to delete user'));
                this.disabled = false;
                this.innerHTML = '<i class="fas fa-trash"></i> Delete';
            }
        });
    });
    
    // Handle reset password buttons
    const resetButtons = document.querySelectorAll('.resetPasswordBtn');
    resetButtons.forEach(btn => {
        btn.addEventListener('click', async function() {
            const userId = this.getAttribute('data-user-id');
            const username = this.getAttribute('data-username');
            
            const newPassword = prompt(`Enter new password for "${username}" (min 6 characters):`);
            
            if (!newPassword) {
                return; // User cancelled
            }
            
            if (newPassword.length < 6) {
                alert('Password must be at least 6 characters!');
                return;
            }
            
            // Disable button
            this.disabled = true;
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Updating...';
            
            // Update password
            const result = await updateUserPassword(userId, newPassword);
            
            if (result.success) {
                alert(result.message || 'Password updated successfully!');
                this.disabled = false;
                this.innerHTML = '<i class="fas fa-key"></i> Reset';
            } else {
                alert('Error: ' + (result.message || 'Failed to update password'));
                this.disabled = false;
                this.innerHTML = '<i class="fas fa-key"></i> Reset';
            }
        });
    });
}
