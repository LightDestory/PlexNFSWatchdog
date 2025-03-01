FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    nfs-common \
    && rm -rf /var/lib/apt/lists/*

COPY ./src /app/src
COPY ./requirements.txt /app/
COPY ./pyproject.toml /app/
COPY ./launch.sh /app/

RUN chmod +x /app/launch.sh

RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["/app/launch.sh"]
