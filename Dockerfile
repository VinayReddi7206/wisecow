# ---------------------------------------------------------------------------
# Wisecow application - Dockerfile
# The app (wisecow.sh) serves fortune|cowsay over HTTP on port 4499 using netcat.
# So the image just needs: bash, fortune, cowsay and an nc that supports -lN.
# ---------------------------------------------------------------------------
FROM debian:bookworm-slim

# Install the runtime prerequisites the script needs.
#  - fortune-mod / fortunes : the `fortune` command + quote database
#  - cowsay                 : the ASCII cow
#  - netcat-openbsd         : provides `nc` with the -N flag used by wisecow.sh
#  - bash                   : the script uses #!/usr/bin/env bash
RUN apt-get update && apt-get install -y --no-install-recommends \
        bash \
        fortune-mod \
        fortunes \
        cowsay \
        netcat-openbsd \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# cowsay and fortune are installed into /usr/games - put it on PATH so the
# script's `command -v cowsay` / `fortune` checks succeed.
ENV PATH="/usr/games:${PATH}"

WORKDIR /app

# Copy the application and make it executable.
COPY wisecow.sh /app/wisecow.sh
RUN chmod +x /app/wisecow.sh

# The app listens on 4499.
EXPOSE 4499

# Run as a non-root user for better security (zero-trust friendly).
RUN useradd -m -u 10001 wisecow
USER wisecow

CMD ["/app/wisecow.sh"]
