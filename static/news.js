// news.js - News viewing functionality (read-only)
// News can only be posted from backend/database

/**
 * Load news list
 */
async function loadNewsList() {
    try {
        const response = await fetch('/api/news/list');
        const data = await response.json();
        
        if (!data.success) {
            console.error('Failed to load news:', data.message);
            return null;
        }
        
        return data;
    } catch (error) {
        console.error('Error loading news:', error);
        return null;
    }
}

/**
 * Mark news as read
 */
async function markNewsRead(newsId) {
    try {
        const response = await fetch(`/api/news/mark-read/${newsId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error marking news as read:', error);
        return { success: false };
    }
}

/**
 * Format date for display
 * @param {string} dateString - ISO date string
 */
function formatNewsDate(dateString) {
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
 * Get role badge color
 */
function getRoleBadgeColor(role) {
    const colors = {
        'master': '#d32f2f',
        'admin': '#fb8c00',
        'super_seller': '#1de9b6',
        'seller': '#00bcd4',
        'all': '#4CAF50'
    };
    return colors[role] || '#888';
}

/**
 * Generate read-only news HTML
 */
async function generateNewsHTML() {
    const newsData = await loadNewsList();
    
    if (!newsData) {
        return `
            <div style="max-width:800px;margin:40px auto 0 auto;padding:32px;background:#fff;border-radius:10px;box-shadow:0 2px 8px rgba(0,0,0,0.07);text-align:center;width:calc(100% - 40px);">
                <h2 style="margin-bottom:24px;color:#d32f2f;">📰 News & Announcements</h2>
                <div style="color:#888;font-size:1.15rem;padding:32px 0;">Error loading news. Please try again.</div>
            </div>
        `;
    }
    
    const newsList = newsData.news || [];
    const unreadCount = newsData.unread || 0;
    
    // Build HTML
    let html = `
        <div style="max-width:900px;margin:40px auto 0 auto;padding:32px;background:#fff;border-radius:10px;box-shadow:0 2px 8px rgba(0,0,0,0.07);width:calc(100% - 40px);">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:24px;flex-wrap:wrap;gap:16px;">
                <div>
                    <h2 style="color:#d32f2f;margin:0;">📰 News & Announcements</h2>
                    <p style="color:#888;margin:5px 0 0 0;font-size:0.95rem;">
                        ${newsList.length} total news
                        ${unreadCount > 0 ? `<span style="background:#fb8c00;color:#fff;padding:2px 8px;border-radius:12px;font-size:0.85rem;margin-left:8px;">${unreadCount} unread</span>` : ''}
                    </p>
                    <p style="color:#999;margin:8px 0 0 0;font-size:0.85rem;font-style:italic;">
                        <i class="fas fa-info-circle"></i> News is posted by system administrators
                    </p>
                </div>
            </div>
            
            <!-- News List -->
            <div id="newsList">
    `;
    
    if (newsList.length === 0) {
        html += `
                <div style="text-align:center;color:#888;padding:60px 20px;font-size:1.1rem;">
                    <i class="fas fa-newspaper" style="font-size:3rem;margin-bottom:16px;color:#ccc;"></i>
                    <p>No news available</p>
                </div>
        `;
    } else {
        newsList.forEach(news => {
            const isUnread = !news.is_read;
            const roleColor = getRoleBadgeColor(news.target_role);
            
            html += `
                <div class="news-item" data-news-id="${news.id}" style="border-left:4px solid ${roleColor};background:${isUnread ? '#fff9e6' : '#fff'};padding:16px;margin-bottom:16px;border-radius:8px;box-shadow:0 1px 4px rgba(0,0,0,0.1);cursor:pointer;transition:all 0.2s;">
                    <div style="display:flex;justify-content:space-between;align-items:start;margin-bottom:12px;flex-wrap:wrap;gap:8px;">
                        <div style="flex:1;">
                            <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;flex-wrap:wrap;">
                                <strong style="color:#333;font-size:1.15rem;">${news.title}</strong>
                                ${isUnread ? '<span style="background:#fb8c00;color:#fff;padding:2px 6px;border-radius:10px;font-size:0.75rem;">NEW</span>' : ''}
                                <span style="background:${roleColor};color:#fff;padding:2px 8px;border-radius:10px;font-size:0.75rem;">${news.target_role.toUpperCase()}</span>
                            </div>
                            <div style="color:#999;font-size:0.85rem;">
                                ${formatNewsDate(news.created_at)}
                                ${news.updated_at !== news.created_at ? ' • Edited' : ''}
                            </div>
                        </div>
                    </div>
                    <div style="color:#555;font-size:0.95rem;line-height:1.6;white-space:pre-wrap;">${news.content}</div>
                </div>
            `;
        });
    }
    
    html += `
            </div>
        </div>
    `;
    
    return html;
}

/**
 * Initialize news functionality
 * Call this after loading news HTML
 */
function initNews() {
    // News item click to mark as read
    document.querySelectorAll('.news-item').forEach(item => {
        item.addEventListener('click', async () => {
            const newsId = item.getAttribute('data-news-id');
            await markNewsRead(newsId);
            
            // Remove unread styling
            item.style.background = '#fff';
            const newBadge = item.querySelector('span[style*="NEW"]');
            if (newBadge && newBadge.textContent === 'NEW') {
                newBadge.remove();
            }
        });
    });
}

/**
 * Show news popup modal on login if there are unread news
 */
async function checkAndShowNewsPopup() {
    try {
        console.log('[NEWS] Checking for unread news...');
        const newsData = await loadNewsList();
        console.log('[NEWS] News data received:', newsData);
        
        if (!newsData || !newsData.news || newsData.news.length === 0) {
            console.log('[NEWS] No news found');
            return; // No news
        }
        
        // Find first unread news
        const unreadNews = newsData.news.find(n => !n.is_read);
        console.log('[NEWS] Unread news:', unreadNews);
        
        if (!unreadNews) {
            console.log('[NEWS] All news already read');
            return; // All news already read
        }
        
        // Show popup modal
        const roleColor = getRoleBadgeColor(unreadNews.target_role);
        
        const modal = document.createElement('div');
        modal.id = 'newsPopupModal';
        modal.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.6);display:flex;align-items:center;justify-content:center;z-index:10000;';
        
        modal.innerHTML = `
            <div style="background:#fff;border-radius:12px;box-shadow:0 8px 32px rgba(0,0,0,0.3);max-width:600px;width:90%;max-height:80vh;overflow-y:auto;animation:slideDown 0.3s ease;">
                <div style="background:${roleColor};color:#fff;padding:20px;border-radius:12px 12px 0 0;">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <h2 style="margin:0;display:flex;align-items:center;gap:10px;">
                            <i class="fas fa-bullhorn"></i>
                            New Announcement
                        </h2>
                        <button id="closeNewsPopup" style="background:rgba(255,255,255,0.2);border:none;color:#fff;font-size:1.5rem;cursor:pointer;width:36px;height:36px;border-radius:50%;transition:all 0.3s;">×</button>
                    </div>
                </div>
                <div style="padding:24px;">
                    <h3 style="color:#333;margin:0 0 12px 0;font-size:1.3rem;">${unreadNews.title}</h3>
                    <div style="color:#999;font-size:0.9rem;margin-bottom:16px;">
                        ${formatNewsDate(unreadNews.created_at)}
                        <span style="background:${roleColor};color:#fff;padding:2px 8px;border-radius:10px;font-size:0.75rem;margin-left:8px;">${unreadNews.target_role.toUpperCase()}</span>
                    </div>
                    <div style="color:#555;font-size:1rem;line-height:1.7;white-space:pre-wrap;border-top:1px solid #eee;padding-top:16px;">
                        ${unreadNews.content}
                    </div>
                    <div style="margin-top:24px;text-align:center;">
                        <button id="markNewsReadBtn" data-news-id="${unreadNews.id}" style="padding:12px 32px;background:${roleColor};color:#fff;border:none;border-radius:8px;cursor:pointer;font-weight:bold;font-size:1rem;transition:all 0.3s;">
                            Got it!
                        </button>
                    </div>
                </div>
            </div>
            <style>
                @keyframes slideDown {
                    from { transform: translateY(-50px); opacity: 0; }
                    to { transform: translateY(0); opacity: 1; }
                }
            </style>
        `;
        
        document.body.appendChild(modal);
        
        // Close button handler
        const closeBtn = document.getElementById('closeNewsPopup');
        const markReadBtn = document.getElementById('markNewsReadBtn');
        
        const closeModal = async () => {
            const newsId = unreadNews.id;
            await markNewsRead(newsId);
            modal.remove();
        };
        
        closeBtn.addEventListener('click', closeModal);
        markReadBtn.addEventListener('click', closeModal);
        
        // Close on outside click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeModal();
            }
        });
        
    } catch (error) {
        console.error('Error checking news popup:', error);
    }
}
