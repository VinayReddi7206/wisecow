FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        bash \
        fortune-mod \
        fortunes \
        cowsay \
        netcat-openbsd \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

ENV PATH="/usr/games:${PATH}"

RUN useradd -m -u 10001 wisecow

WORKDIR /app

COPY wisecow.sh /app/wisecow.sh
RUN chmod +x /app/wisecow.sh && chown -R wisecow:wisecow /app

EXPOSE 4499

USER wisecow

CMD ["/app/wisecow.sh"]