-- ============================================
-- NEWS POSTING SCRIPT
-- ============================================
-- Use this script to post news from backend/MySQL
-- News can only be posted from backend - users cannot post from dashboard
--
-- When you insert a new news for a target_role, the application will
-- automatically delete all previous news for that same target_role.
-- This ensures only the latest news exists for each role.
-- ============================================

-- INSTRUCTIONS:
-- 1. Connect to MySQL: mysql -u root -p
-- 2. Select database: USE tatkal_db;
-- 3. Copy and modify one of the examples below
-- 4. Execute the INSERT statement
-- 5. Old news for same target_role will be auto-deleted by the application

-- ============================================
-- EXAMPLES: Post news for different roles
-- ============================================

-- Example 1: Post news for ALL users (master, admin, super_seller, seller)
INSERT INTO news (author_id, title, content, target_role) 
VALUES (
    47,  -- author_id (use a master user's ID, e.g., 47, 48, 49, 50, or 51)
    'System Maintenance Notice',
    'Our system will undergo maintenance on Sunday, November 24, 2025 from 2:00 AM to 4:00 AM. Please plan accordingly. Thank you for your patience!',
    'all'
);

-- Example 2: Post news for MASTER only
INSERT INTO news (author_id, title, content, target_role) 
VALUES (
    47,
    'New Feature Update',
    'Dear Masters,

We have added new dashboard analytics features. You can now see real-time statistics and improved hierarchy management.

Best regards,
System Administrator',
    'master'
);

-- Example 3: Post news for ADMIN only
INSERT INTO news (author_id, title, content, target_role) 
VALUES (
    47,
    'Admin Training Session',
    'All admins are requested to join the online training session on November 25, 2025 at 10:00 AM. Link will be shared via email.',
    'admin'
);

-- Example 4: Post news for SUPER_SELLER only
INSERT INTO news (author_id, title, content, target_role) 
VALUES (
    47,
    'Sales Target Update',
    'Monthly sales target has been increased by 15%. New incentive structure is now active. Check with your admin for details.',
    'super_seller'
);

-- Example 5: Post news for SELLER only
INSERT INTO news (author_id, title, content, target_role) 
VALUES (
    47,
    'Key Creation Guidelines',
    'Please ensure all keys are properly activated and paid before marking them active. Verify customer details carefully.

Thank you!',
    'seller'
);

-- ============================================
-- BEFORE POSTING: Get User IDs
-- ============================================
-- To find valid author_id (must be a master user):
SELECT id, username, role FROM users WHERE role = 'master';

-- Sample output:
-- +----+----------+--------+
-- | id | username | role   |
-- +----+----------+--------+
-- | 47 | master   | master |
-- | 48 | master2  | master |
-- | 49 | master3  | master |
-- | 50 | master4  | master |
-- | 51 | master5  | master |
-- +----+----------+--------+

-- ============================================
-- QUICK NEWS POST TEMPLATE
-- ============================================
-- Copy this and fill in the details:

INSERT INTO news (author_id, title, content, target_role) 
VALUES (
    47,                          -- Change to valid master user ID
    'Your Title Here',           -- News title
    'Your news content here.     -- News content (can be multi-line)
You can write multiple lines.
Add details as needed.',
    'all'                        -- Target: 'all', 'master', 'admin', 'super_seller', 'seller'
);

-- ============================================
-- VIEW ALL NEWS
-- ============================================
SELECT 
    n.id,
    n.title,
    n.target_role,
    n.created_at,
    u.username as posted_by
FROM news n
JOIN users u ON n.author_id = u.id
WHERE n.is_active = 1
ORDER BY n.created_at DESC;

-- ============================================
-- DELETE ALL NEWS FOR A SPECIFIC ROLE
-- ============================================
-- This is automatically done when posting new news,
-- but you can manually delete if needed:

-- Delete all news for 'admin' role:
DELETE FROM news_read WHERE news_id IN (SELECT id FROM news WHERE target_role = 'admin');
DELETE FROM news WHERE target_role = 'admin';

-- Delete all news for 'seller' role:
DELETE FROM news_read WHERE news_id IN (SELECT id FROM news WHERE target_role = 'seller');
DELETE FROM news WHERE target_role = 'seller';

-- ============================================
-- NOTES:
-- ============================================
-- 1. target_role options: 'all', 'master', 'admin', 'super_seller', 'seller'
-- 2. When users login for the first time after news is posted, they see a popup
-- 3. News is saved in News tab ordered by date
-- 4. Only ONE news per target_role exists (old ones auto-deleted)
-- 5. Use author_id from master users (IDs: 47-51)
