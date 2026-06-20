# Data Analytics Bot
Telegram-бот для автоматического анализа данных с использованием ИИ-агента.

## Описание проекта
Бот принимает CSV или Excel файлы, проводит глубокий анализ данных и возвращает структурированный PDF-отчет с инсайтами и визуализациями.

## Запуск

### 1. Клонирование репозитория

```bash
git clone https://github.com/yourusername/DataAnalytics_bot.git
cd DataAnalytics_bot
```

### 2. Создание виртуального окружения

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
```

### 3. Установка зависимостей 

```bash
pip install -r requirements.txt
```

### 4. Настройка

Необходимо создать файл `.env` в корне проекта:

```env
API_KEY=your_api_key

BOT_TOKEN=your_telegram_bot_token
```
### 5. Установка шрифтов для PDF

Скачайте шрифты DejaVu и поместите их в папку fonts/

### 6. Запуск

Запустите скрипт:

```bash
python main.py
```

