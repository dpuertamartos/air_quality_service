FROM python:3.11-slim

WORKDIR /usr/src/app

COPY ./app ./app
COPY ./data ./data
COPY ./requirements.txt .

RUN pip install --no-cache-dir -r ./requirements.txt

EXPOSE 5000
CMD ["gunicorn", "-c", "app/config/main.py", "app.main:app"]