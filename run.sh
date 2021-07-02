#!/bin/bash
set -e 

  RETRIES=10

  echo "Connecting to ${DATABASE_URL}"
  until psql ${DATABASE_URL} -c "select 1" > /dev/null 2>&1 || [ $RETRIES -eq 0 ]; do
    echo "Waiting for postgres server, $((RETRIES--)) remaining attempts..."
    sleep 10
  done

  cd /usr/src/app/
  python runthread.py

