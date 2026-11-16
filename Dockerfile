FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 TZ=Europe/Berlin
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl tini chromium chromium-driver && rm -rf /var/lib/apt/lists/*
WORKDIR /opt/mightymouse
COPY mightymouse/ /opt/mightymouse/
COPY controller/ /opt/controller/
RUN pip install --no-cache-dir requests selenium qbittorrent-api schedule bencodepy tqdm
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh && mkdir -p /config /staging /watch /blocked /data/mam-seed
ENTRYPOINT ["/usr/bin/tini","--","/entrypoint.sh"]
