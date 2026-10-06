<div align="center">

# 🏁 Indy Carts

**Card trading game for IndyCar fans in Telegram**

**Collect. Trade. Risk. Become a paddock legend.**

---

<!-- ═══════════════════════════════════════════ -->
<!-- TECH STACK · TechIcons (Dark theme)        -->
<!-- Source: github.com/gui-bus/TechIcons       -->
<!-- ═══════════════════════════════════════════ -->

<p align="center">
  <a href="https://www.python.org/"><img alt="Python" height="52" width="52" src="https://github.com/gui-bus/TechIcons/blob/main/Dark/Python.svg"></a>
  <a href="https://aiogram.dev/"><img alt="aiogram" height="52" width="52" src="https://github.com/gui-bus/TechIcons/blob/main/Dark/Aiogram.svg"></a>
  <a href="https://fastapi.tiangolo.com/"><img alt="FastAPI" height="52" width="52" src="https://github.com/gui-bus/TechIcons/blob/main/Dark/FastAPI.svg"></a>
  <a href="https://www.postgresql.org/"><img alt="PostgreSQL" height="52" width="52" src="https://github.com/gui-bus/TechIcons/blob/main/Dark/PostgreSQL.svg"></a>
  <a href="https://www.sqlalchemy.org/"><img alt="SQLAlchemy" height="52" width="52" src="https://github.com/gui-bus/TechIcons/blob/main/Dark/SQLAlchemy.svg"></a>
  <a href="https://www.docker.com/"><img alt="Docker" height="52" width="52" src="https://github.com/gui-bus/TechIcons/blob/main/Dark/Docker.svg"></a>
  <a href="https://render.com/"><img alt="Render" height="52" width="52" src="https://github.com/gui-bus/TechIcons/blob/main/Dark/Render.svg"></a>
  <a href="https://supabase.com/"><img alt="Supabase" height="52" width="52" src="https://github.com/gui-bus/TechIcons/blob/main/Dark/Supabase.svg"></a>
</p>

---

<!-- ═══════════════════════════════════════════ -->
<!-- BADGES · Shields.io                        -->
<!-- Source: shields.io                         -->
<!-- ═══════════════════════════════════════════ -->

<p align="center">
  <img alt="Version" src="https://img.shields.io/badge/version-1.2.0-orange?style=for-the-badge&logo=github&logoColor=white">
  <img alt="License" src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge&logo=opensourceinitiative&logoColor=white">
  <img alt="Status" src="https://img.shields.io/badge/status-active-brightgreen?style=for-the-badge">
  <img alt="Players" src="https://img.shields.io/badge/players-31-blue?style=for-the-badge">
</p>

<p align="center">
  <a href="https://t.me/IndyCarts_bot"><img src="https://img.shields.io/badge/Telegram_Bot-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white" alt="Telegram Bot"></a>
  <a href="https://t.me/IndyCarts"><img src="https://img.shields.io/badge/Telegram_Channel-26A5E4?style=for-the-badge&logo=telegram&logoColor=white" alt="Telegram Channel"></a>
  <a href="https://github.com/kimi-svga/indycarts"><img src="https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white" alt="GitHub"></a>
</p>

---

<!-- ═══════════════════════════════════════════ -->
<!-- TOOLS · Simple Icons                       -->
<!-- Source: simpleicons.org                    -->
<!-- ═══════════════════════════════════════════ -->

<p align="center">
  <img alt="Git" height="36" src="https://cdn.simpleicons.org/git/F05032">
  <img alt="GitHub Actions" height="36" src="https://cdn.simpleicons.org/githubactions/2088FF">
  <img alt="Bash" height="36" src="https://cdn.simpleicons.org/gnubash/4EAA25">
  <img alt="Redis" height="36" src="https://cdn.simpleicons.org/redis/DC382D">
  <img alt="Nginx" height="36" src="https://cdn.simpleicons.org/nginx/009639">
</p>

---

</div>

## 📖 About

**Indy Carts** is an unofficial fan project by **P4/9 Development**.

A Telegram card game where players collect IndyCar driver cards, trade on a live market, battle in PvP duels, and take loans from **P4/9 Bank**.

> **Not affiliated** with IndyCar, its teams, drivers, or rights holders.
> All cards are hand-drawn in a custom style.

**Bot:** [@IndyCarts_bot](https://t.me/IndyCarts_bot)
**Channel:** [@IndyCarts](https://t.me/IndyCarts)

---

## ✨ Features

### 🃏 Cards & Collection

- **7 rarities** — Basic, Rare, Epic, Mythic, Legendary, Limited, Season
- **Limited supply** — Limited & Season cards have `max_supply`
- **Serial numbers** — each limited card has `#1/50`
- **INDY Winner (IW)** — rare overlay, ×3 price multiplier
- **Merge 3→1** — Legendary → Limited with 20% chance

### 💹 Live Market

- Price depends on **demand & supply**
- **Price history** — 1h / 6h / 24h / 7 days
- **Decay** to base price (every 10 minutes)
- **Market events** — admin can boost/drop prices
- **Sale fee** — 10%

### ⚔️ PvP Seasons

- **Season lasts 1 month** — rating reset every month
- **Multi-stakes** — up to **3 cards** per side
- **Money stakes** — winner takes all
- **Elo rating** — 6 titles from Rookie to Legend
- **Top-10 rewards** — coins + attempts + exclusive card
- **Eternal titles** — «👑 Champion S1» stays forever
- **Automated** — cron ends season and creates new one

### 🏦 P4/9 Bank 2.0

- **Loans** — up to **1,000,000** coins
- **Dynamic rate** — 15–30% of amount
- **Trust score** — rating with 6 ranks
- **Refinancing** — move debt to new term
- **Early repayment** — 2% discount
- **Overdue** — trust −15, 3 days to pay
- **Default** — 10 cards confiscated, PvP block 7 days
- **FAQ inside bank** — 9 topics

### 💎 Indy+ Subscription

- **Price:** 20 ⭐ / 200,000 coins
- **Duration:** 30 days
- **Bonuses:**
  - +5 daily attempts (instead of 2)
  - ×1.2 PvP rating
  - 7% royalty on creator cards
  - 5% auction commission
  - +10% rare drop chance
  - Exclusive card every month
  - Priority support

### 🛡 Support System

- **Tickets** — player creates, support responds
- **8 categories** — bug, balance, cards, PvP, bank, Indy+, report, other
- **Auto-priority** — bug/balance/cards → urgent
- **Support panel** — filters, stats, replies
- **FAQ** — quick answers before ticket
- **Roles** — 5 levels: owner, admin, moderator, helper, support

### 🔨 Ban Hammer

- **3 levels:** warn → mute → ban
- **Auto-rules:** profanity, spam, wintrading
- **Punishment history** — all actions logged
- **Auto-lift** — bans expire automatically

---

## 🚀 Quick Start

### 1. Clone

```bash
git clone https://github.com/kimi-svga/indycarts.git
cd indycarts
```

2. Virtual environment

```bash
python -m venv .venv
source .venv/bin/activate  # Linux / macOS
.venv\Scripts\activate     # Windows
```

3. Dependencies

```bash
pip install -r requirements.txt
```

4. Configure environment

```bash
cp .env.example .env
```

Fill in .env:

Variable Description
BOT_TOKEN Token from @BotFather
DATABASE_URL PostgreSQL URL (Supabase)
WEBHOOK_URL Service URL on Render
WEBHOOK_SECRET Webhook secret
OWNER_IDS Owner Telegram IDs (JSON)
ADMIN_IDS Admin Telegram IDs (JSON)

5. Run

```bash
python main.py
```

---

🌐 Deploy on Render

1. Web Service

· Repository: your GitHub repo
· Build Command: pip install -r requirements.txt
· Start Command: python main.py
· Environment: Python 3.12

2. Environment Variables

All keys from .env.example → Render → Environment.

3. Webhook

Webhook is set automatically on start.

Check: https://your-app.onrender.com/health

---

🎮 Commands

Player

Command Description
/start Register / menu
/menu Main menu
/help Help by role
/support Support (tickets)
/promo Activate promo code
/loan 50000 Take a loan
/repay 5000 Repay loan
/refinance Refinance
/duel @user Challenge to PvP

Admin

Command Description
/admin Admin panel
/hire @user role Assign role
/fire @user Remove role
/ban @user 30d reason Ban 30 days
/mute @user 24h reason Mute 24 hours
/warn @user reason Warning
/unban @user Lift punishment
/banlist Active punishments
/userinfo @user Player card
/givecard @user ID Give card
/resetpvp @user Reset PvP
/broadcast Broadcast
/announce text Post to channel
/stats General stats

Owner

Command Description
/setbalance @user N Set balance
/addmoney @user N Add coins
/giveaway @user N Gift
/setseasonreward Season rewards
/event ID multiplier Market event
/support_panel Support panel

Full list — /help in bot.

---

🧮 Price Formula

```
Price = base_price × (demand / supply) × event × IW_multiplier
```

Limits:

```
floor = base_price × 0.3
ceiling = base_price × 5.0
```

Base prices:

Rarity Base
🔵 Basic 100
🟢 Rare 300
🟣 Epic 1,000
🟠 Mythic 5,000
🟡 Legendary 20,000
🔴 Limited 50,000
⭐ Season 100,000

---

🛠️ Stack

· Python 3.12
· aiogram 3.x — Telegram bot
· FastAPI — webhook server
· SQLAlchemy 2.0 (async) — ORM
· PostgreSQL (Supabase) — database
· Render — hosting
· GitHub Pages — riddle sites (Creator)

---

📁 Project Structure

```
indycarts/
├── bot/
│   ├── handlers/       # Command handlers
│   ├── keyboards/      # Keyboards
│   ├── middlewares/    # Middleware (log, user, ban)
│   └── utils/          # Utilities (stable, decorators, actions)
├── core/
│   ├── config.py       # Settings (pydantic-settings)
│   ├── constants.py    # Game constants
│   ├── logger.py       # Logger
│   └── exceptions.py   # Custom exceptions
├── db/
│   ├── models.py       # SQLAlchemy models
│   └── session.py      # AsyncSession
├── services/
│   ├── drop.py         # Drop logic
│   ├── economy.py      # Price formulas
│   ├── market.py       # Market
│   ├── merge.py        # Card merge
│   ├── pvp.py          # Elo & seasons
│   └── bank.py         # Loans
├── main.py             # Entry point
├── requirements.txt
├── .env.example
└── README.md
```

---

🗺️ Roadmap

✅ Done (v1.2.0)

☑ Registration with usernames
☑ Cards + drop + 7 rarities
☑ Card editor + bulk upload
☑ Daily bonus + streaks
☑ Market (buy/sell)
☑ Live market (demand/supply)
☑ PvP duels with Elo
☑ Bank with loans & trust score
☑ Promo codes
☑ Referral system
☑ Indy+ subscription (20 ⭐ / 200k coins)
☑ PvP seasons with auto-rewards
☑ Ban Hammer (warn/mute/ban)
☑ Roles (5 levels)
☑ Support System (tickets + panel)
☑ Statistics (6 commands)
☑ /help by role

⏳ In Progress (v1.3.0+)

☐ 🎭 Creator S1 — players create cards, get royalties
☐ 🏰 Social — clans, auction, trading
☐ 🧩 Matchmaking — quick opponent finder
☐ 🏎️ F1 cards — mixed series
☐ 🎯 Quests & achievements
☐ 📱 WebApp — mobile version

---

🤝 Contributing

Pull Requests are welcome.

What you can do

· Bugs — open Issue with template
· Features — first discuss in Issue, then PR
· Documentation — README edits, comments
· Tests — pytest for services

What we don't accept

· Secrets in commits
· Spam features (casino, betting)
· Huge PRs (>500 lines without discussion)

More details — CONTRIBUTING.md.
---

👥 Team

· P4/9 Development — code, architecture, economy
· Gabi — card design, logo, visuals

---

📜 License

Code — MIT. See LICENSE.

What's NOT under MIT:

· 🎨 Cards and graphics — property of Indy Carts
· 🏷️ Name «Indy Carts» and logo — property of Indy Carts

---

💬 Links

· Bot: @IndyCarts_bot
· Channel: @IndyCarts
· Issues: GitHub Issues

---

<div align="center">

P4/9 Development · 2026

Made with 🏁 for the IndyCar community

</div>
