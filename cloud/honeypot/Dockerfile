FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir requests
COPY public_http.py .
EXPOSE 8080
CMD ["python3", "public_http.py"]
