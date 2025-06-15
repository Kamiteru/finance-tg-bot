# Telegram Finance Bot 💰

A comprehensive personal finance assistant for tracking income and expenses with advanced multi-currency support.

## ⚡ Key Features

### 💸 Financial Management
- ➕ Add income and expense transactions
- 📊 Detailed statistics with interactive charts
- 📈 View recent transactions history
- 🔒 Encrypted financial data storage
- 💱 Multi-currency support with real-time conversion

### 🎯 Goal Management
- 💼 Create and track financial goals
- 📈 Monitor progress with visual indicators
- ⏰ Set deadlines for goals
- ✅ Automatic achievement notifications

### ⏰ Smart Reminders
- 📅 Create payment reminders
- 🔔 Automatic notifications at scheduled times
- 📋 View and manage active reminders

### 💱 Currency Converter
- 🌍 Real-time exchange rates
- 💰 Convert between multiple currencies
- 📈 Popular currency pairs display
- 🔧 Customizable currency preferences

### 📄 Export & Reports
- 📊 Export data to PDF format
- 📈 Export to Excel spreadsheets
- 📋 Detailed statistics with summaries

### 📝 Category Management
- ➕ Create custom income/expense categories
- 📋 View all categories by type
- 🏷️ Default categories on first setup

### 👤 User Preferences
- 💱 Set preferred display currency
- 🔧 Customize converter currency list
- 🌐 Per-user data isolation

## 🚀 Installation & Setup

### 1. Clone Repository
```bash
git clone <repository-url>
cd telegram-finance-bot
```

### 2. Create Virtual Environment
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
Create `.env` file in project root:
```env
BOT_TOKEN=your_telegram_bot_token_here
DATABASE_URL=sqlite:///finance.db
ENCRYPTION_KEY_FILE=crypto.key
```

### 5. Get Bot Token
1. Find @BotFather in Telegram
2. Create new bot with `/newbot`
3. Copy token to `.env` file

### 6. Initialize Database
```bash
# Apply migrations
alembic upgrade head
```

### 7. Start Bot
```bash
python main.py
```

## 🐳 Docker Deployment

### 1. Build Image
```bash
docker-compose build
```

### 2. Run Container
```bash
docker-compose up -d
```

## 📱 Bot Usage

### First Launch
1. Send `/start` to bot
2. Default categories are created automatically
3. Use menu buttons for navigation

### Main Commands
- `/start` - Start bot and show main menu
- `/add_income` - Add income transaction
- `/add_expense` - Add expense transaction
- `/stats` - Display statistics with charts
- `/view_transactions` - Show recent transactions
- `/set_goal` - Create financial goal
- `/view_goals` - View and manage goals
- `/add_reminder` - Create payment reminder
- `/view_reminders` - View active reminders
- `/convert` - Currency converter
- `/export` - Export financial reports
- `/set_currency` - Change display currency
- `/add_category` - Create custom category

### Interface Navigation
Convenient keyboard with buttons:
- 💰 ➕ Income / 💸 ➖ Expense
- 📊 Statistics
- 🎯 💼 Goals  
- 💱 💸 Converter
- 📝 Categories
- ⏰ Reminders
- 📄 Export

## 🔧 Architecture

### Project Structure
```
├── main.py              # Application entry point
├── config.py            # Configuration settings
├── handlers/            # Message handlers
│   ├── base.py         # Base handlers and menu
│   ├── transaction.py  # Transaction management
│   ├── goal.py         # Financial goals
│   ├── reminder.py     # Payment reminders
│   ├── converter.py    # Currency converter
│   └── reports.py      # Report generation
├── services/           # Business logic
│   ├── transaction.py  # Transaction service
│   ├── goal.py         # Goal service
│   ├── reminder.py     # Reminder service
│   ├── converter.py    # Currency service
│   ├── user.py         # User management
│   ├── crypto.py       # Data encryption
│   └── scheduler.py    # Task scheduler
├── database/           # Database layer
│   ├── models.py       # SQLAlchemy models
│   └── db.py          # Database connection
├── reports/            # Report generation
│   └── export.py       # PDF/Excel export
└── alembic/           # Database migrations
```

### Technology Stack
- **aiogram 3.3.0** - Telegram Bot API framework
- **SQLAlchemy 2.0.21** - Database ORM
- **SQLite** - Database engine
- **Alembic 1.12.0** - Database migrations
- **Cryptography 41.0.4** - Data encryption
- **APScheduler 3.10.4** - Task scheduling
- **matplotlib 3.7.2** - Statistical charts
- **pandas 2.0.3** - Data processing
- **reportlab 4.0.4** - PDF generation
- **openpyxl 3.1.2** - Excel export
- **requests 2.31.0** - HTTP requests for currency rates
- **python-dotenv 1.0.0** - Environment variables

## 🔒 Security Features

- **Data Encryption**: All transaction amounts encrypted in database
- **Multi-user Support**: Complete data isolation between users
- **Input Validation**: Comprehensive validation of user inputs
- **Error Handling**: Robust API and network error handling
- **Secure Storage**: Encrypted sensitive financial data

## 📊 Advanced Features

- **Multi-user Architecture**: Each user has isolated data
- **Real-time Currency**: Live exchange rates for conversions
- **Smart Statistics**: Interactive charts and detailed analytics
- **Automated Reminders**: Scheduled notifications system
- **Data Export**: Professional PDF and Excel reports
- **Customizable Interface**: User-defined categories and currencies
- **Encrypted Storage**: All financial amounts secured with encryption

## 🌍 Currency Support

Supported currencies:
- USD ($) - US Dollar
- EUR (€) - Euro
- RUB (₽) - Russian Ruble
- GBP (£) - British Pound
- CNY (¥) - Chinese Yuan
- JPY (¥) - Japanese Yen
- KZT (₸) - Kazakhstani Tenge
- BYN (Br) - Belarusian Ruble

Users can:
- Set preferred display currency
- Customize converter currency list
- View statistics in chosen currency
- Convert between any supported currencies

## 🐛 Debugging & Logs

Logs are saved to `bot.log` file. To view errors:
```bash
tail -f bot.log
```

## 📝 Development

### Create New Migration
```bash
alembic revision --autogenerate -m "description"
```

### Apply Migrations
```bash
alembic upgrade head
```

### Run Tests
```bash
pytest tests/
```

## 🤝 Support

If you encounter issues:
1. Check logs in `bot.log`
2. Verify bot token is correct
3. Ensure internet connection for currency converter
4. Check database permissions

## 📄 License

MIT License 