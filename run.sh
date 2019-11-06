#!/bin/bash
set -e 

  RETRIES=10

  until psql -h ${POSTGRES_HOST} -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "select 1" > /dev/null 2>&1 || [ $RETRIES -eq 0 ]; do
    echo "Waiting for postgres server, $((RETRIES--)) remaining attempts..."
    sleep 1
  done

  psql -h ${POSTGRES_HOST} -U ${POSTGRES_USER} -d ${POSTGRES_DB} -f /usr/src/app/${POSTGRES_DB}.pgsql
  echo "Data from ${POSTGRES_DB}.pgsql has been imported"

  cd /usr/src/app/
  python runthread.py

