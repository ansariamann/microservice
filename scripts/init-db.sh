#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "userdb_dev" <<-EOSQL
    CREATE DATABASE notificationdb_dev;
EOSQL
