#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Generates a self-signed TLS certificate for wisecow.local and creates the
# Kubernetes TLS secret "wisecow-tls" that the Ingress uses for HTTPS.
#
# Usage:
#     chmod +x gen-certs.sh
#     ./gen-certs.sh
# ---------------------------------------------------------------------------
set -euo pipefail

HOST="wisecow.local"
CERT_DIR="./certs"
mkdir -p "$CERT_DIR"

echo ">> Generating a self-signed certificate for ${HOST} ..."
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout "${CERT_DIR}/tls.key" \
  -out "${CERT_DIR}/tls.crt" \
  -subj "/CN=${HOST}/O=wisecow" \
  -addext "subjectAltName=DNS:${HOST}"

echo ">> Creating/updating the Kubernetes TLS secret 'wisecow-tls' ..."
kubectl create secret tls wisecow-tls \
  --cert="${CERT_DIR}/tls.crt" \
  --key="${CERT_DIR}/tls.key" \
  --dry-run=client -o yaml | kubectl apply -f -

echo ">> Done. Secret 'wisecow-tls' is ready for the Ingress."
