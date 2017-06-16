#!/bin/sh

echo "Wiating for MySQL to start for 10 sec"
sleep 10
code_base="/code"

while true; do
 echo "================================="
 echo "Running reports bundle at: `date`"
 cd /${code_base} && ./report.sh && ./jira.sh && ./ssheet.sh || (echo "Failed to execute" && exit 10)
 echo "Done. Sleeping 5 mins"
 echo "================================="
 echo ""
 echo ""
 sleep 5m
done