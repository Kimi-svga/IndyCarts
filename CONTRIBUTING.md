# Contributing to Indy Carts

First off — **thank you** for considering contributing to Indy Carts!

This document explains how to contribute in a way that keeps the project clean, fast, and enjoyable for everyone.

---

## 📖 Table of Contents

- [Code of Conduct](#-code-of-conduct)
- [How Can I Contribute?](#-how-can-i-contribute)
- [Reporting Bugs](#-reporting-bugs)
- [Suggesting Features](#-suggesting-features)
- [Pull Requests](#-pull-requests)
- [Style Guide](#-style-guide)
- [Commit Convention](#-commit-convention)
- [Project Structure](#-project-structure)
- [License](#-license)

---

## 🤝 Code of Conduct

By participating, you agree to:

- Be **respectful** to other contributors.
- **Not** use offensive language.
- **Not** spam PRs or Issues.
- **Not** push secrets, tokens, or private data.

Violations → **ban** from the repository.

---

## 💡 How Can I Contribute?

You can help in many ways:

| Type | What to do |
|------|-----------|
| 🐛 **Bug report** | Open an Issue with reproduction steps |
| 💡 **Feature idea** | Open an Issue, discuss first |
| 🔧 **Code** | Open a Pull Request |
| 📖 **Docs** | Fix README, comments, or wiki |
| 🎨 **Design** | Suggest card designs, icons, UI |
| 🧪 **Tests** | Add pytest coverage for services |
| 🌍 **Translation** | Translate bot text (future) |

---

## 🐛 Reporting Bugs

Before opening an Issue:

1. **Search** existing [Issues](https://github.com/kimi-svga/indycarts/issues) — maybe it's already reported.
2. **Check** the latest version — bug may be fixed.
3. **Reproduce** the bug locally.

When opening an Issue, include:

- **Title** — short, clear, no emojis-only.
- **Steps** to reproduce.
- **Expected** behavior.
- **Actual** behavior.
- **Screenshots** (if UI-related).
- **Logs** (if available).
- **Environment** — OS, Python version, bot version.

**Template:**

```markdown
**Describe the bug**
A clear and concise description.

**To Reproduce**
1. Go to '...'
2. Click on '...'
3. See error

**Expected behavior**
What you expected to happen.

**Screenshots**
If applicable.

**Environment:**
- OS: [e.g. Windows 11]
- Python: [e.g. 3.12.0]
- Bot version: [e.g. 1.2.0]
```

---

💡 Suggesting Features

1. Check Issues — maybe it's already suggested.
2. Open a new Issue with [Feature] prefix.
3. Describe:
   · What you want.
   · Why it's useful.
   · How it might work.
4. Wait for maintainer approval before coding.

⚠️ Do not open a PR for a feature without prior discussion.

---

🔧 Pull Requests

Step 1 — Fork & Clone

```bash
git clone https://github.com/YOUR_USERNAME/indycarts.git
cd indycarts
git remote add upstream https://github.com/kimi-svga/indycarts.git
```

Step 2 — Create a Branch

```bash
git checkout -b feature/my-feature
```

Branch naming:

Prefix Use for
feature/ New feature
fix/ Bug fix
refactor/ Code refactor
docs/ Documentation
test/ Tests
chore/ Maintenance

Step 3 — Write Code

Follow the Style Guide.

Rules:

· 1 PR = 1 feature.
· Don't mix multiple features in one PR.
· Test locally before pushing.
· Update CHANGELOG.md (if applicable).

Step 4 — Commit

Follow the Commit Convention.

Step 5 — Push & Open PR

```bash
git push origin feature/my-feature
```

Open a Pull Request on GitHub.

Step 6 — PR Review

· Maintainer reviews within 48 hours.
· Address feedback in new commits (do not force-push after review).
· Once approved — squash merge into main.

---

📋 PR Checklist

Before submitting, ensure:

☐ Code works locally.
☐ No secrets in commits (.env, tokens, keys).
☐ No card assets in commits (assets/cards/).
☐ PEP 8 style followed.
☐ Type hints added for new functions.
☐ Docstrings added (Russian, project standard).
☐ Commit message follows convention.
☐ CHANGELOG.md updated (if user-facing).
☐ README.md updated (if new commands / features).

---

🎨 Style Guide

Python

· PEP 8 strictly.
· Line length — 100 characters max.
· Quotes — double " preferred.
· Imports — sorted (stdlib → third-party → local).
· Type hints — required for new functions.
· Docstrings — Russian, project standard.

Example:

```python
async def get_user_balance(session: AsyncSession, telegram_id: int) -> int:
    """Возвращает баланс игрока по telegram_id."""
    user = (await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )).scalar_one_or_none()

    return user.balance if user else 0
```

File Naming

· Snake_case for Python files: support_panel.py.
· Lowercase for directories: handlers/, keyboards/.

Bot Text

· HTML for formatting (<b>, <i>, <code>).
· Emoji — at the start of the line, not middle.
· Capital letters for headers.

---

📝 Commit Convention

Format:

```
type: short description

Optional body

Optional footer
```

Types:

Type Use for
feat New feature
fix Bug fix
docs Documentation
style Formatting (no logic change)
refactor Code refactoring
test Tests
chore Maintenance (deps, config)
perf Performance improvements

Examples:

```
feat: add Indy+ subscription

- Subscription model
- Telegram Stars payment
- subscription_check_task
```

```
fix: resolve Challenger card selection in PvP

Challenger now receives "Choose cards" button after /duel.
```

```
docs: update README with support system
```

---

📁 Project Structure

```
indycarts/
├── bot/
│   ├── handlers/       # Command handlers
│   ├── keyboards/      # Inline keyboards
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

Where to add new code:

What Where
New bot command bot/handlers/
New keyboard bot/keyboards/
New business logic services/
New DB model db/models.py
New constant core/constants.py
New setting core/config.py

---

🚨 What We Don't Accept

· Secrets in commits (.env, tokens, keys).
· Card assets in commits (assets/cards/, *.psd).
· Spam features (casino, betting, gambling).
· Huge PRs (>500 lines without discussion).
· Plagiarized code without attribution.
· AI-generated slop without review.
· Breaking API changes without warning.

---

🧪 Testing

Local testing:

```bash
python main.py
```

Test checklist before PR:

☐ /start works
☐ Main features work
☐ No errors in logs
☐ Database migrations applied
☐ No console warnings

Future: pytest for services (services/drop.py, services/economy.py, etc.).

---

🔐 Security

Never commit:

· .env file
· Bot tokens
· Database URLs
· Webhook secrets
· Owner / Admin IDs

If you accidentally commit a secret:

1. Revoke the token immediately (@BotFather → /revoke).
2. Change DB password (Supabase).
3. Rewrite git history:
   ```bash
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch .env" \
     --prune-empty --tag-name-filter cat -- --all
   ```
4. Force push to remote.

---

📜 License

By submitting a Pull Request, you agree that your contribution is licensed under the MIT License.

---

💬 Questions?

· Telegram: @IndyCarts
· GitHub Issues: Open an issue
· Bot: @IndyCarts_bot

---

<div align="center">

P4/9 Development · 2026

Thanks for contributing! 🏁
