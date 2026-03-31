FROM python:3.13-slim-bookworm

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY ./cskg4apt/ .

EXPOSE 8000

EXPOSE 57623-57628

CMD ["python3", "cskg4apt/app.py"]
