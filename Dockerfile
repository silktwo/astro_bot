FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates && rm -rf /var/lib/apt/lists/*

# Swiss Ephemeris дані (достатній набір для планет 1800-2400)
RUN mkdir -p /app/ephe && cd /app/ephe && \
    for f in sepl_18.se1 semo_18.se1 seas_18.se1; do \
      curl -fsSL "https://github.com/aloistr/swisseph/raw/master/ephe/$f" -o "$f"; \
    done

WORKDIR /app
COPY pyproject.toml .
COPY src ./src
COPY data ./data
RUN pip install --no-cache-dir .

ENV SWISSEPH_PATH=/app/ephe
CMD ["python", "-m", "astro_bot.bot"]
