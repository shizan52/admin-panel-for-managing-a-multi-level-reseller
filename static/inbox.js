// inbox.js - Inbox functionality for all dashboards

/**
 * Load inbox messages
 */
async function loadInboxMessages() {
    try {
        const response = await fetch('/api/inbox/messages');
        const data = await response.json();
        
        if (!data.success) {
            console.error('Failed to load messages:', data.message);
            return null;
        }
        
        return data;
    } catch (error) {
        console.error('Error loading inbox:', error);
        return null;
    }
}

/**
 * Send a new message
 * @param {string} toUsername - Recipient username
 * @param {string} subject - Message subject
 * @param {string} message - Message content
 */
async function sendMessage(toUsername, subject, message) {
    try {
        const response = await fetch('/api/inbox/send', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                to_username: toUsername,
                subject: subject,
                message: message
            })
        });
        
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error sending message:', error);
        return { success: false, message: 'Connection error' };
    }
}

/**
 * Mark message as read
 * @param {number} messageId - Message ID
 */
async function markAsRead(messageId) {
    try {
        const response = await fetch(`/api/inbox/mark-read/${messageId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error marking message:', error);
        return { success: false };
    }
}

/**
 * Delete a message
 * @param {number} messageId - Message ID
 */
async function deleteMessage(messageId) {
    try {
        const response = await fetch(`/api/inbox/delete/${messageId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error deleting message:', error);
        return { success: false };
    }
}

/**
 * Get list of users current user can send messages to
 */
async function getUsersList() {
    try {
        const response = await fetch('/api/users/list');
        const data = await response.json();
        
        if (!data.success) {
            return [];
        }
        
        return data.users || [];
    } catch (error) {
        console.error('Error fetching users:', error);
        return [];
    }
}

/**
 * Format date for display
 * @param {string} dateString - ISO date string
 */
function formatDate(dateString) {
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
 * Generate inbox HTML
 */
async function generateInboxHTML() {
    const inboxData = await loadInboxMessages();
    const usersList = await getUsersList();
    
    if (!inboxData) {
        return `
            <div style="max-width:800px;margin:40px auto 0 auto;padding:32px;background:#fff;border-radius:10px;box-shadow:0 2px 8px rgba(0,0,0,0.07);text-align:center;width:calc(100% - 40px);">
                <h2 style="margin-bottom:24px;color:#d32f2f;">Inbox</h2>
                <div style="color:#888;font-size:1.15rem;padding:32px 0;">Error loading inbox. Please try again.</div>
            </div>
        `;
    }
    
    const messages = inboxData.messages || [];
    const unreadCount = inboxData.unread || 0;
    
    // Advanced Search UI
    let html = `
        <div style="max-width:900px;margin:40px auto 0 auto;padding:32px;background:#fff;border-radius:10px;box-shadow:0 2px 8px rgba(0,0,0,0.07);width:calc(100% - 40px);">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:24px;flex-wrap:wrap;gap:16px;">
                <div>
                    <h2 style="color:#d32f2f;margin:0;">Inbox</h2>
                    <p style="color:#888;margin:5px 0 0 0;font-size:0.95rem;">
                        ${messages.length} total messages
                        ${unreadCount > 0 ? `<span style=\"background:#fb8c00;color:#fff;padding:2px 8px;border-radius:12px;font-size:0.85rem;margin-left:8px;\">${unreadCount} unread</span>` : ''}
                    </p>
                </div>
                ${usersList.length > 0 ? `<button id="composeMessageBtn" style="padding:10px 20px;background:#1de9b6;color:#222;border:none;border-radius:8px;cursor:pointer;font-weight:bold;transition:all 0.3s;font-size:0.95rem;"><i class=\"fas fa-envelope\" style=\"margin-right:8px;\"></i>Compose Message</button>` : ''}
            </div>
            <div style="margin-bottom:24px;background:#f5f5f5;padding:18px 16px;border-radius:8px;">
                <form id="userSearchForm" style="display:flex;gap:12px;flex-wrap:wrap;align-items:center;">
                    <select id="searchType" style="padding:8px 10px;border-radius:6px;border:1px solid #ccc;font-size:15px;">
                        <option value="userid">User ID</option>
                        <option value="mac">MAC Address</option>
                        <option value="secret_key">Secret Key</option>
                    </select>
                    <input type="text" id="searchQuery" placeholder="Enter User ID, MAC, or Secret Key" style="flex:1;min-width:180px;padding:8px 10px;border-radius:6px;border:1px solid #ccc;font-size:15px;">
                    <button type="submit" style="padding:8px 18px;background:#00bcd4;color:#fff;border:none;border-radius:6px;cursor:pointer;font-weight:bold;">Search</button>
                </form>
                <div id="userSearchResult" style="margin-top:14px;"></div>
            </div>
            <div id="composeMessageForm" style="display:none;background:#f5f5f5;padding:20px;border-radius:8px;margin-bottom:24px;">
                <h3 style="margin-top:0;color:#333;">New Message</h3>
                <form id="sendMessageForm">
                    <div style="margin-bottom:16px;">
                        <label style="display:block;margin-bottom:6px;font-weight:600;color:#555;">To:</label>
                        <select id="messageRecipient" required style="width:100%;padding:10px;border-radius:6px;border:1px solid #ccc;font-size:16px;">
                            <option value="">Select recipient...</option>
                            ${usersList.map(user => `<option value="${user.username}">${user.username} (${user.role})</option>`).join('')}
                        </select>
                    </div>
                    <div style="margin-bottom:16px;">
                        <label style="display:block;margin-bottom:6px;font-weight:600;color:#555;">Subject:</label>
                        <input type="text" id="messageSubject" required style="width:calc(100% - 22px);padding:10px;border-radius:6px;border:1px solid #ccc;font-size:16px;" placeholder="Enter subject">
                    </div>
                    <div style="margin-bottom:16px;">
                        <label style="display:block;margin-bottom:6px;font-weight:600;color:#555;">Message:</label>
                        <textarea id="messageBody" required rows="4" style="width:calc(100% - 22px);padding:10px;border-radius:6px;border:1px solid #ccc;font-size:16px;resize:vertical;" placeholder="Enter your message"></textarea>
                    </div>
                    <div style="display:flex;gap:12px;">
                        <button type="submit" style="padding:10px 20px;background:#4CAF50;color:#fff;border:none;border-radius:6px;cursor:pointer;font-weight:bold;transition:all 0.3s;">Send Message</button>
                        <button type="button" id="cancelComposeBtn" style="padding:10px 20px;background:#888;color:#fff;border:none;border-radius:6px;cursor:pointer;font-weight:bold;transition:all 0.3s;">Cancel</button>
                    </div>
                </form>
            </div>
            <div id="messagesList">`;
    if (messages.length === 0) {
        html += `<div style=\"color:#888;font-size:1.15rem;padding:32px 0;text-align:center;\">No messages found.</div>`;
    } else {
        // Render each message as a card
        html += `<div style=\"display:flex;flex-direction:column;gap:12px;\">`;
        for (const msg of messages) {
            const when = msg.created_at ? formatDate(msg.created_at) : '';
            html += `
                <div class="message-item" data-message-id="${msg.id}" style="background:#fff;padding:16px;border-radius:8px;box-shadow:0 1px 4px rgba(0,0,0,0.04);cursor:pointer;border:1px solid #f0f0f0;">
                    <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:12px;">
                        <div style="flex:1;min-width:0;">
                            <div style="display:flex;align-items:center;gap:10px;">
                                <div style=\"font-weight:700;color:#333;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:420px;\">${msg.from_username || 'Unknown'}</div>
                                <div style=\"color:#666;font-size:0.95rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:420px;\">&nbsp;—&nbsp;${msg.subject}</div>
                            </div>
                            <div style="color:#777;font-size:0.9rem;margin-top:8px;">${msg.message}</div>
                            <div style="color:#999;font-size:0.8rem;margin-top:8px;">${when}</div>
                        </div>
                        <div style="display:flex;flex-direction:column;align-items:flex-end;gap:8px;">
                            ${!msg.is_read ? `<span style=\"background:#fb8c00;color:#fff;padding:4px 8px;border-radius:12px;font-size:0.75rem;\">NEW</span>` : ''}
                            <button class="deleteMessageBtn" data-message-id="${msg.id}" style="padding:6px 10px;background:#e53935;color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:0.85rem;">Delete</button>
                        </div>
                    </div>
                </div>
            `;
        }
        html += `</div>`;
    }
    html += `</div></div>`;
    return html;
}
    /**
     * Initialize inbox UI event handlers. Call this after injecting inbox HTML into the page.
     */
    function initInbox() {
        const composeForm = document.getElementById('composeMessageForm');
        const composeBtn = document.getElementById('composeMessageBtn');
        const cancelComposeBtn = document.getElementById('cancelComposeBtn');
        const sendForm = document.getElementById('sendMessageForm');
        const userSearchForm = document.getElementById('userSearchForm');
        const userSearchResult = document.getElementById('userSearchResult');

        // Ensure compose area hidden initially
        if (composeForm) composeForm.style.display = 'none';
        if (composeBtn) composeBtn.style.display = 'inline-block';

        // Compose button shows form
        if (composeBtn && composeForm) {
            composeBtn.addEventListener('click', () => {
                composeForm.style.display = '';
                composeBtn.style.display = 'none';
                const recipientSelect = document.getElementById('messageRecipient');
                if (recipientSelect) recipientSelect.value = '';
                window.scrollTo({ top: composeForm.offsetTop - 60, behavior: 'smooth' });
            });
        }

        // Cancel compose
        if (cancelComposeBtn && composeForm) {
            cancelComposeBtn.addEventListener('click', () => {
                composeForm.style.display = 'none';
                if (composeBtn) composeBtn.style.display = 'inline-block';
                if (sendForm) sendForm.reset();
            });
        }

        // User search form (search by userid / mac / secret_key)
        if (userSearchForm && userSearchResult) {
            userSearchForm.addEventListener('submit', async function (e) {
                e.preventDefault();
                const type = document.getElementById('searchType').value;
                const query = document.getElementById('searchQuery').value.trim();
                if (!query) {
                    userSearchResult.innerHTML = '<span style="color:#d32f2f;">Please enter a search value.</span>';
                    return;
                }
                userSearchResult.innerHTML = '<span style="color:#888;">Searching...</span>';
                try {
                    const res = await fetch(`/api/inbox/user-search?type=${encodeURIComponent(type)}&query=${encodeURIComponent(query)}`);
                    const data = await res.json();
                    if (!data.success) {
                        userSearchResult.innerHTML = `<span style="color:#d32f2f;">${data.error || 'User not found.'}</span>`;
                    } else {
                        const user = data.user;
                        userSearchResult.innerHTML = `
                            <div style="background:#fff;padding:16px;border-radius:8px;box-shadow:0 1px 4px rgba(0,0,0,0.07);margin-top:4px;">
                                <div style="font-weight:bold;font-size:1.1rem;">User ID: <span style="color:#00bcd4;">${user.username}</span></div>
                                <div>MAC Address: <span style="color:#fb8c00;">${user.mac_address || 'N/A'}</span></div>
                                <div>Role: <span style="color:#444;">${user.role}</span></div>
                                <button class="sendDirectMessageBtn" data-uid="${user.username}" style="margin-top:10px;padding:8px 18px;background:#4CAF50;color:#fff;border:none;border-radius:6px;cursor:pointer;font-weight:bold;">Send Message</button>
                            </div>
                        `;

                        // Attach handler to open compose and preselect recipient
                        const btn = userSearchResult.querySelector('.sendDirectMessageBtn');
                        if (btn && composeForm) {
                            btn.addEventListener('click', () => {
                                composeForm.style.display = '';
                                if (composeBtn) composeBtn.style.display = 'none';
                                const recipientSelect = document.getElementById('messageRecipient');
                                if (recipientSelect) recipientSelect.value = user.username;
                                window.scrollTo({ top: composeForm.offsetTop - 60, behavior: 'smooth' });
                            });
                        }
                    }
                } catch (err) {
                    userSearchResult.innerHTML = '<span style="color:#d32f2f;">Search failed.</span>';
                }
            });
        }

        // Send message form submission
        if (sendForm) {
            sendForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const recipient = document.getElementById('messageRecipient').value;
                const subject = document.getElementById('messageSubject').value;
                const message = document.getElementById('messageBody').value;

                const submitBtn = sendForm.querySelector('button[type="submit"]');
                submitBtn.disabled = true;
                submitBtn.textContent = 'Sending...';

                const result = await sendMessage(recipient, subject, message);

                if (result.success) {
                    alert('Message sent successfully!');
                    sendForm.reset();
                    if (composeForm) composeForm.style.display = 'none';
                    if (composeBtn) composeBtn.style.display = 'inline-block';

                    // Reload inbox content
                    const newHTML = await generateInboxHTML();
                    const dashboardContent = document.getElementById('dashboardContent');
                    if (dashboardContent) {
                        dashboardContent.innerHTML = newHTML;
                        // Re-init handlers on new content
                        initInbox();
                    }
                } else {
                    alert('Failed to send message: ' + result.message);
                    submitBtn.disabled = false;
                    submitBtn.textContent = 'Send Message';
                }
            });
        }

        // Attach message item click handlers (mark read) and delete buttons within current DOM
        document.querySelectorAll('.message-item').forEach(item => {
            item.addEventListener('click', async (e) => {
                if (e.target.classList.contains('deleteMessageBtn')) return;
                const messageId = item.getAttribute('data-message-id');
                await markAsRead(messageId);
                item.style.background = '#fff';
                const newBadge = item.querySelector('span');
                if (newBadge && newBadge.textContent === 'NEW') newBadge.remove();
            });
        });

        document.querySelectorAll('.deleteMessageBtn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.stopPropagation();
                if (!confirm('Are you sure you want to delete this message?')) return;
                const messageId = btn.getAttribute('data-message-id');
                const result = await deleteMessage(messageId);
                if (result.success) {
                    const newHTML = await generateInboxHTML();
                    const dashboardContent = document.getElementById('dashboardContent');
                    if (dashboardContent) {
                        dashboardContent.innerHTML = newHTML;
                        initInbox();
                    }
                } else {
                    alert('Failed to delete message: ' + result.message);
                }
            });
        });
    }

    // Export initInbox for callers
    window.initInbox = initInbox;

