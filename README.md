<div align="center">

```
██╗   ██╗███████╗███╗   ██╗ ██████╗ ███╗   ███╗
██║   ██║██╔════╝████╗  ██║██╔═══██╗████╗ ████║
██║   ██║█████╗  ██╔██╗ ██║██║   ██║██╔████╔██║
╚██╗ ██╔╝██╔══╝  ██║╚██╗██║██║   ██║██║╚██╔╝██║
 ╚████╔╝ ███████╗██║ ╚████║╚██████╔╝██║ ╚═╝ ██║
  ╚═══╝  ╚══════╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝     ╚═╝
```

```
     ▄▄▄████████▄▄▄
   ▄████████████████▄
  ████████████████████
  ███   ████████   ███
  ███   ████████   ███
  ▀████▄▄ ▀██▀ ▄▄████▀
    ▀██████████████▀
     ██ ██ ██ ██ ██
     ▀▀ ▀▀ ▀▀ ▀▀ ▀▀
```

**VENOM — multi-tier reseller & access-key management dashboard**

![backend: Flask](https://img.shields.io/badge/backend-Flask-black) ![database: MySQL](https://img.shields.io/badge/database-MySQL-blue) ![auth: bcrypt](https://img.shields.io/badge/auth-bcrypt-success) ![frontend: vanilla JS](https://img.shields.io/badge/frontend-vanilla%20JS-yellow)

```
backend  ..... Python · Flask · Flask-Session
database ..... MySQL
auth     ..... bcrypt + server-side sessions
frontend ..... vanilla JS · HTML · CSS (light / dark)
roles    ..... 5-tier hierarchy, each manages only the one below
size     ..... app.py: 3,275 lines · 52 routes
```

</div>

> A self-hosted panel for managing a **hierarchy of resellers**: each role creates and manages only the layer directly below
> it, issues and controls **access keys** for an external application, and keeps everyone informed through an internal inbox
> and role-targeted news. Originally built for a ticket-booking software vendor.

```
▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄
```

## ▓▒░ ROLE LADDER  (each role manages only the one below) ░▒▓

```
┌──────────────┐
│ SUPER MASTER │
└──────────────┘
        │
        ▼
┌──────────────┐
│    MASTER    │
└──────────────┘
        │
        ▼
┌──────────────┐
│    ADMIN     │
└──────────────┘
        │
        ▼
┌──────────────┐
│ SUPER SELLER │
└──────────────┘
        │
        ▼
┌──────────────┐
│    SELLER    │
└──────────────┘
```

Higher roles see and act on their own sub-tree only — isolation is enforced on the server, not just hidden in the UI.

## ▓▒░ THREE CORE SYSTEMS ░▒▓

```
╔══════════════════════════════════════════════════════════════════════════════════════╗
║ [KEY]   Access keys  9-digit token + password, device (IP / MAC) binding,            ║
║                      activation windows of 7 / 15 / 30 / 60 / 90 days,               ║
║                      full audit trail of every success, failure and blocked attempt  ║
║ [MAIL]  Inbox         role-aware messaging, compose / read / delete, unread tracking ║
║ [NEWS]  News          per role or broadcast; a newer item replaces the older one     ║
╚══════════════════════════════════════════════════════════════════════════════════════╝
```

## ▓▒░ QUICK START ░▒▓

```
╔═══════════════════════════════════════════════════════════╗
║ pip install -r requirements.txt                           ║
║ mysql -u root -p < setup_mysql.sql                        ║
║ # edit config.py with your own MySQL credentials          ║
║ python app.py                     # http://127.0.0.1:5000 ║
╚═══════════════════════════════════════════════════════════╝
```

> **Heads-up:** `templates/` (the HTML pages `app.py` renders) is **not included** in this copy — add your own before running. `static/` holds the front-end logic.

## ▓▒░ LAYOUT ░▒▓

```
path             what it is
───────────────────────────────────────────────────────────────────────────────
app.py           Flask app + all API routes
config.py        MySQL + session configuration
post_news.py     post and manage news from the terminal
setup_mysql.sql  creates the database and the MySQL user
setup.ps1        one-shot Windows setup
static/          auth · inbox · keys · news · profile · user-management (+ CSS)
QUICK_GUIDE.txt  walkthrough, test checklist and the API reference
```

## ▓▒░ SECURITY ░▒▓

This is a **demo-grade** project. Before using it with real data:

- Change **every** default / seeded account password (they are listed in `QUICK_GUIDE.txt` for local testing only).
- Replace the MySQL credentials in `config.py` and `setup_mysql.sql` with strong, unique ones.
- `SECRET_KEY` is generated with `os.urandom(24)` at start-up, so sessions end on every restart — persist a secret if you need them to survive.
- Put it behind HTTPS and a reverse proxy.

**Licence.** Personal / private project — no licence is granted for reuse without the author's permission.

```
▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄
```
