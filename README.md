# 🏁 Indy Carts

**Card trading game for IndyCar fans in Telegram**

[![Version](https://img.shields.io/badge/version-0.5-orange?style=for-the-badge)](https://github.com/your-username/indycarts)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![aiogram](https://img.shields.io/badge/aiogram-3.x-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)](https://aiogram.dev/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

**Collect. Trade. Risk. Become a paddock legend.**

</div>

---

## 📖 About

**Indy Carts** is an unofficial fan project by **P4/9 Development**.  
A card game in Telegram where players collect IndyCar driver cards, trade on a live market, battle in PvP duels, and take loans from **P4/9 Bank**.

> **Not affiliated** with IndyCar, its teams, drivers, or rights holders.  
> All cards are hand-drawn in a custom style.

---

## ✨ Features

| | |
|---|---|
| 🃏 **Driver cards** | Rarities from Common to Ultra |
| ⭐ **INDY Winner** | Overlay that boosts card value |
| 🎴 **Drop** | 2 attempts per day |
| 💹 **Market** | Buy/sell with 3% fee |
| 📊 **Live prices** | Supply/demand formula |
| ⚔️ **PvP duels** | Dice rolls, winner takes a card |
| 🏦 **P4/9 Bank** | Loans at 10% |
| 🏆 **Leaderboard** | Top-10 by balance |
| 📅 **Daily bonus** | 450 coins + 2 attempts |
| 🎁 **Promo codes** | Rewards for codes |
| 🎨 **Card builder** | Add cards via bot |
| 📦 **Bulk upload** | JSON file with cards |

---

## 🚀 Quick Start

```bash
git clone https://github.com/your-username/indycarts.git
cd indycarts
pip install -r requirements.txt
python main.py
```

Environment Variables

Variable Description
BOT_TOKEN Bot token from @BotFather
DATABASE_URL PostgreSQL connection string
WEBHOOK_URL Service URL on Render
WEBHOOK_SECRET Webhook secret
ADMIN_IDS Admin Telegram IDs (JSON array)

---

🎮 Commands

Command Description
/start Register / main menu
/promo CODE Activate promo code
/duel @user Challenge to PvP
/loan 5000 Take a loan
/buy ID Buy a card
/sell ID Sell a card

---

🧮 Price Formula

```
Price = base_price × (demand / supply) × event × IW
```

Rarities:

Rarity Base Price
Common 100
Rare 300
Epic 1 000
Legendary 5 000
Ultra 20 000

---

🛠️ Stack

· Python 3.12
· aiogram 3.x
· FastAPI
· SQLAlchemy 2.0 (async)
· PostgreSQL
· Docker
· Render

---

📁 Project Structure

```
indycarts/
├── bot/
│   ├── handlers/       # Command handlers
│   ├── keyboards/      # Keyboards
│   └── middlewares/    # Middleware
├── core/
│   ├── config.py       # Config
│   ├── constants.py    # Constants
│   └── logger.py       # Logging
├── db/
│   ├── models.py       # SQLAlchemy models
│   └── session.py      # DB connection
├── services/
│   ├── drop.py         # Drop logic
│   └── economy.py      # Price formulas
├── main.py             # Entry point
├── Dockerfile
├── requirements.txt
└── README.md
```

---

🗺️ Roadmap


☑ Registration with usernames

☑ Cards + drop with photo

☑ Card builder

☑ Daily bonus

☑ Market (buy/sell)

☑ PvP duels

☑ Bank with loans

☑ Promo codes

☑ Bulk upload

☐ Demand/supply tracking

☐ Limited items (helmets, cars, podiums)

☐ Seasons and resets

☐ News analyzer



🤝 Contributing

Pull requests are welcome.
For major changes, please open an issue first.

Guidelines:

· Clean code
· Meaningful commits
· Tests when possible

---

👥 Team

· P4/9 Development — code, architecture, economy

· Gabi — card design, logo, visuals

---

📜 License

MIT — see LICENSE for details.

---

<div align="center">

P4/9 Development · 2026

</div>
```
