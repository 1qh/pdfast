FROM python:slim
WORKDIR /app
COPY . .
RUN pip install fastapi uvicorn python-multipart pdf-tocgen pypdf