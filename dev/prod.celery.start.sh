#!/bin/bash

cd ~/celery_project

for keyval in $(cat .env | sed -e 's/: /=/g' -e "s/'\|,\|{\|}//g" -e 's/", "/ /g' -e 's/"}//g' ); do export $keyval; done

celery -A shapeworks_cloud.celery worker -n "w1@${HOSTNAME}" -Q gpu --logfile=celery-logs
