FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt
COPY . .
ENV PORT=8000
EXPOSE 8000
CMD ["sh","-c","uvicorn engine_reference:app --host 0.0.0.0 --port ${PORT}"]
