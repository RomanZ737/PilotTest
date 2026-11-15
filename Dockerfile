FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Зависимости для сборки mysqlclient
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# Убедитесь, что gunicorn добавлен в requirements.txt!
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Создаем папку для логов (чтобы Django не падал при старте)
RUN mkdir -p log

# Собираем статику для Whitenoise
RUN python manage.py collectstatic --noinput




# Запускаем Gunicorn (замените PilotTest, если папка называется иначе)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "PilotTest.wsgi:application"]