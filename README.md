# VENOM Dashboard

A Flask-based multi-tier reseller & access-key management dashboard, originally built for a Tatkal (Indian Railway) ticket-booking service. It gives a business a self-hosted panel to manage a hierarchy of resellers, issue and control license/access keys for an external booking tool, and keep everyone in the chain informed through internal messaging and announcements.

## Overview

The dashboard is organized around a strict role hierarchy — **Super Master → Master → Admin → Super Seller → Seller** — where each role can only create, view, and manage the roles directly below it. This keeps each branch of the reseller tree isolated: a Master only ever sees their own downline, never another Master's.

On top of that hierarchy sit three core systems:

- **Access Key Management** — Each key is a 9-digit access token (with its own name and password) that an external application (the ticket-booking tool) validates against. Keys are locked to a single device (IP/MAC), can be activated for a fixed duration (7–90 days), and every access attempt is logged for auditing.
- **Inbox / Messaging** — Role-aware internal messaging so higher roles can broadcast instructions or updates down the chain (e.g., Master → Admin → Super Seller → Seller), with read/unread tracking per user.
- **News & Announcements** — Targeted announcements per role (or broadcast to everyone), with automatic replacement of older news for the same audience so each role always sees the latest notice.

## Features

- Role-based dashboards (Super Master, Master, Admin, Super Seller, Seller) with strict hierarchy isolation
- User creation & management restricted to the layer directly below the acting role
- 9-digit access-key issuing system with password protection, device (IP/MAC) binding, and activation windows
- Full access-key audit trail (per-key access history, success/failure/blocked attempts)
- Internal inbox with compose/read/delete and unread indicators
- Role-targeted news/announcements with read tracking
- Session-based auth with bcrypt password hashing
- Light/dark mode support

## Tech Stack

- **Backend:** Python, Flask, Flask-Session
- **Database:** MySQL (via `mysql-connector-python`)
- **Auth:** bcrypt password hashing, server-side sessions
- **Frontend:** Vanilla JavaScript, HTML templates, CSS

## Project Structure

```
tatkal/
├── app.py              # Flask application & all API routes
├── config.py            # MySQL connection & session configuration
├── post_news.py         # CLI tool to post/manage news from the terminal
├── post_news.sql        # SQL reference snippets for posting news directly
├── setup_mysql.sql      # Creates the database and MySQL user
├── setup.ps1             # One-shot PowerShell setup script (Windows)
├── requirements.txt      # Python dependencies
├── QUICK_GUIDE.txt       # Full walkthrough: setup, roles, testing checklist
└── static/
    ├── auth.js
    ├── dashboard.css
    ├── inbox.js
    ├── keys.js
    ├── news.js
    ├── profile.js
    └── user-management.js
```

> **Note:** This copy of the repository includes the backend and static assets only. The HTML `templates/` folder referenced by `app.py` is not included here — add your own templates (or restore them from your working copy) before running the app.

## Setup

1. **Install dependencies**
   ```powershell
   pip install -r requirements.txt
   ```

2. **Create the database**
   ```powershell
   mysql -u root -p < setup_mysql.sql
   ```

3. **Configure the connection**
   Edit `config.py` with your own MySQL credentials before running anything against a real database.

4. **Run the app**
   ```powershell
   python app.py
   ```
   The dashboard will be available at `http://127.0.0.1:5000`.

For a full walkthrough — including the default seeded accounts, step-by-step tests for the inbox/news/keys systems, and the complete API reference — see [`QUICK_GUIDE.txt`](QUICK_GUIDE.txt).

## Security Notes

- Change every default/seeded account password immediately if you deploy this anywhere beyond local testing.
- Update the MySQL credentials in `config.py` and `setup_mysql.sql` to strong, unique values before any real deployment.
- `app.config['SECRET_KEY']` is currently generated with `os.urandom(24)` at process start, which means sessions are invalidated on every restart — swap this for a persisted secret if you need sessions to survive a redeploy.

## License

Personal / private project — no license granted for reuse without permission from the author.
