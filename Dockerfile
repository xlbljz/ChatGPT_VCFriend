FROM python:3.11-alpine
WORKDIR /app
COPY . .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt
CMD ["python", "wecom_recieve.py"]
EXPOSE 80