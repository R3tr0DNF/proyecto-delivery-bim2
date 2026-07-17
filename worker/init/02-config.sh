#!/bin/bash
set -e

echo "Configurando pg_hba.conf..."

cat >> "$PGDATA/pg_hba.conf" <<EOF
host    all    all    172.16.0.0/12    trust
host    all    all    192.168.0.0/24   trust
EOF

echo "Configuración aplicada."

