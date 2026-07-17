#!/bin/bash
set -e

echo "Configurando pg_hba.conf..."

sed -i '/^host[[:space:]]\+all[[:space:]]\+all[[:space:]]\+all[[:space:]]\+scram-sha-256/i\
host    all    all    172.16.0.0/12    trust\
host    all    all    192.168.0.0/24   trust
' "$PGDATA/pg_hba.conf"

echo "Configuración aplicada."