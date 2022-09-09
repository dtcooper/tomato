#!/bin/sh

if [ ! -f /.env ]; then
    echo 'No .env file found. Exiting!'
    exit 1
fi


if [ $# = 0 ]; then
    ./manage.py runserver
else
    exec "$@"
fi
