FROM python:3.11-slim

RUN useradd -m -d /home/app -s /bin/bash app

WORKDIR /home/app

RUN apt-get update && apt-get install -y \
    nfs-common \
    && rm -rf /var/lib/apt/lists/*

COPY . /home/app/
COPY launch.sh /home/app/launch.sh
RUN chown -R app:app /home/app
RUN chmod +x /home/app/launch.sh

USER app
RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["/home/app/launch.sh"]
