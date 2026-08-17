#!/usr/bin/env python
"""
News Posting Tool
=================
Use this script to post news from command line.
News will be posted to the database and users will see it on first login.

Usage:
    python post_news.py

Requirements:
    - MySQL database must be running
    - config.py must have correct database credentials
"""

import mysql.connector
from config import MYSQL_CONFIG
from datetime import datetime

def get_db_connection():
    """Create database connection"""
    return mysql.connector.connect(**MYSQL_CONFIG)

def get_master_users():
    """Get list of master users"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT id, username FROM users WHERE role = %s', ('master',))
    masters = cursor.fetchall()
    conn.close()
    return masters

def delete_old_news(target_role):
    """Delete all old news for a target role"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get old news IDs
    cursor.execute('SELECT id FROM news WHERE target_role = %s', (target_role,))
    old_news_ids = [row['id'] for row in cursor.fetchall()]
    
    if old_news_ids:
        placeholders = ','.join(['%s'] * len(old_news_ids))
        # Delete from news_read first (foreign key)
        cursor.execute(f'DELETE FROM news_read WHERE news_id IN ({placeholders})', tuple(old_news_ids))
        # Delete from news
        cursor.execute(f'DELETE FROM news WHERE id IN ({placeholders})', tuple(old_news_ids))
        conn.commit()
        print(f"✅ Deleted {len(old_news_ids)} old news for '{target_role}'")
    else:
        print(f"ℹ️  No old news found for '{target_role}'")
    
    conn.close()

def post_news(author_id, title, content, target_role):
    """Post a new news item"""
    try:
        # Delete old news for this target_role
        delete_old_news(target_role)
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Insert new news
        cursor.execute('''
            INSERT INTO news (author_id, title, content, target_role)
            VALUES (%s, %s, %s, %s)
        ''', (author_id, title, content, target_role))
        
        news_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print(f"\n{'='*60}")
        print(f"✅ NEWS POSTED SUCCESSFULLY!")
        print(f"{'='*60}")
        print(f"News ID: {news_id}")
        print(f"Target Role: {target_role}")
        print(f"Title: {title}")
        print(f"Posted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error posting news: {str(e)}\n")
        return False

def view_all_news():
    """View all active news"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute('''
        SELECT 
            n.id,
            n.title,
            n.target_role,
            n.created_at,
            u.username as posted_by
        FROM news n
        JOIN users u ON n.author_id = u.id
        WHERE n.is_active = 1
        ORDER BY n.created_at DESC
    ''')
    
    news_items = cursor.fetchall()
    conn.close()
    
    if not news_items:
        print("\nℹ️  No news found in database\n")
        return
    
    print(f"\n{'='*80}")
    print(f"ALL ACTIVE NEWS")
    print(f"{'='*80}")
    for news in news_items:
        print(f"ID: {news['id']} | Role: {news['target_role']:15} | Posted by: {news['posted_by']}")
        print(f"Title: {news['title']}")
        print(f"Date: {news['created_at']}")
        print(f"{'-'*80}")
    print()

def main():
    """Main interactive menu"""
    print("\n" + "="*60)
    print("📰 NEWS POSTING TOOL")
    print("="*60)
    
    # Get master users
    masters = get_master_users()
    if not masters:
        print("❌ No master users found in database!")
        return
    
    while True:
        print("\nOptions:")
        print("1. Post new news")
        print("2. View all news")
        print("3. Exit")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == '1':
            # Post news
            print("\n" + "-"*60)
            print("POST NEW NEWS")
            print("-"*60)
            
            # Select author (master user)
            print("\nAvailable master users:")
            for i, master in enumerate(masters, 1):
                print(f"{i}. {master['username']} (ID: {master['id']})")
            
            try:
                author_choice = int(input(f"\nSelect author (1-{len(masters)}): ").strip())
                if author_choice < 1 or author_choice > len(masters):
                    print("❌ Invalid choice!")
                    continue
                author_id = masters[author_choice - 1]['id']
            except ValueError:
                print("❌ Invalid input!")
                continue
            
            # Select target role
            print("\nTarget roles:")
            roles = [
                ('all', 'All users (master, admin, super_seller, seller)'),
                ('master', 'Masters only'),
                ('admin', 'Admins only'),
                ('super_seller', 'Super Sellers only'),
                ('seller', 'Sellers only')
            ]
            
            for i, (role_value, role_desc) in enumerate(roles, 1):
                print(f"{i}. {role_desc}")
            
            try:
                role_choice = int(input(f"\nSelect target role (1-{len(roles)}): ").strip())
                if role_choice < 1 or role_choice > len(roles):
                    print("❌ Invalid choice!")
                    continue
                target_role = roles[role_choice - 1][0]
            except ValueError:
                print("❌ Invalid input!")
                continue
            
            # Get title
            title = input("\nEnter news title: ").strip()
            if not title:
                print("❌ Title cannot be empty!")
                continue
            
            # Get content
            print("\nEnter news content (press Enter twice to finish):")
            content_lines = []
            while True:
                line = input()
                if line == "" and content_lines and content_lines[-1] == "":
                    content_lines.pop()  # Remove last empty line
                    break
                content_lines.append(line)
            
            content = "\n".join(content_lines).strip()
            if not content:
                print("❌ Content cannot be empty!")
                continue
            
            # Confirm
            print("\n" + "="*60)
            print("CONFIRM NEWS POST")
            print("="*60)
            print(f"Target Role: {target_role}")
            print(f"Title: {title}")
            print(f"Content:\n{content}")
            print("="*60)
            
            confirm = input("\nPost this news? (y/n): ").strip().lower()
            if confirm == 'y':
                post_news(author_id, title, content, target_role)
            else:
                print("❌ News posting cancelled.")
        
        elif choice == '2':
            # View news
            view_all_news()
        
        elif choice == '3':
            # Exit
            print("\n👋 Goodbye!\n")
            break
        
        else:
            print("❌ Invalid choice! Please enter 1, 2, or 3.")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!\n")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}\n")
