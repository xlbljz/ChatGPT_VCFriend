FROM python:3.11.0
WORKDIR /app
COPY . .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get update && apt-get install -y ffmpeg libavcodec-extra
CMD ["python", "main.py"]
EXPOSE 80