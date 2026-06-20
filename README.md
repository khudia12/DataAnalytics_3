# Data Analytics Bot
Telegram-бот для автоматического анализа данных с использованием ИИ-агента.


## Описание проекта
Бот принимает CSV или Excel файлы, проводит глубокий анализ данных и возвращает структурированный PDF-отчет с инсайтами и визуализациями.


## Возможности

- Загрузка данных - поддержка CSV и Excel файлов

- LLM-агент самостоятельно исследует данные

- Визуализация - автоматическое создание графиков и диаграмм

- PDF-отчеты с графиками и инсайтами

- Добавление инструкции

- Защита от prompt-injection - безопасная обработка пользовательских запросов

## Технологии

- Python 3.10+ - основной язык

- LangChain - фреймворк для LLM-агентов

- OpenAI GPT-4o-mini - модель

- Pandas - работа с данными

- Matplotlib/Seaborn - визуализация

- python-telegram-bot - Telegram бот


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

## Использование
1. Для начала работы отправьте команду /start

2. Отправьте CSV или Excel файл

3. По желанию добавьте инструкцию - текстовое сообщение с указанием, на что обратить внимание

4. Для запуска анализа отправьте команду /analyze

5.  бот пришлет PDF-отчет с анализом

## Инструменты агента
Агент использует следующие инструменты для анализа:
- get_schema - Получение структуры датасета
- sample_data - Просмотр примеров записей
- get_missing - Анализ пропущенных значений
- get_numeric_stats - Статистика числовых признаков
- get_categorical_stats - Статистика категориальных признаков
- get_correlations - Корреляционный анализ
- detect_outliers - Обнаружение выбросов
- execute_python - Выполнение Python кода для анализа
- create_visualization - Создание графиков

## Демонстрация запуска и результата


## Пример 1 (из видео)
Датасет:


Отчёт:
[analysis_report.pdf](https://github.com/user-attachments/files/29162306/analysis_report.pdf)


## Пример 2
Датасет:

Отчёт:
[analysis_report_2.pdf](https://github.com/user-attachments/files/29162310/analysis_report_2.pdf)
