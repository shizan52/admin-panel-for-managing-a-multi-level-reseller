// auth.js - Common authentication utilities for all dashboards

/**
 * Check if user is authenticated
 * Redirects to login if not authenticated
 */
async function checkAuth() {
    try {
        const response = await fetch('/api/session-check');
        const data = await response.json();
        
        if (!data.authenticated) {
            window.location.href = '/login';
            return null;
        }
        
        return data.user;
    } catch (error) {
        console.error('Auth check failed:', error);
        window.location.href = '/login';
        return null;
    }
}

/**
 * Handle user logout
 * Clears session and redirects to login
 */
async function handleLogout() {
    if (!confirm('Are you sure you want to sign out?')) {
        return;
    }
    
    try {
        const response = await fetch('/api/logout', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Clear any client-side storage
            sessionStorage.clear();
            localStorage.removeItem('theme'); // Optional: keep theme preference
            
            // Redirect to login
            window.location.href = data.redirect || '/login';
        } else {
            alert('Logout failed: ' + data.message);
        }
    } catch (error) {
        console.error('Logout error:', error);
        alert('Logout failed. Please try again.');
    }
}

/**
 * Update user info in topbar
 * @param {Object} user - User object with username and role
 */
function updateUserInfo(user) {
    const userInfoElement = document.querySelector('.user-info');
    if (userInfoElement && user) {
        userInfoElement.textContent = user.username;
    }
}

// Auto-check authentication on page load
window.addEventListener('DOMContentLoaded', async function() {
    const user = await checkAuth();
    if (user) {
        updateUserInfo(user);
    }
});

// Alias for backward compatibility
function logout() {
    handleLogout();
}
