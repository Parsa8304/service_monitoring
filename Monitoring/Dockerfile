FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV DJANGO_SETTINGS_MODULE=monitoring_api.settings
EXPOSE 8000
CMD ["gunicorn","monitoring_api.wsgi:application","--bind","0.0.0.0:8000"]
