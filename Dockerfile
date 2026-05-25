FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --upgrade setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt
COPY app.py .
EXPOSE 5000
CMD ["python", "app.py"]