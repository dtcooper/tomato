#!/bin/sh

if [ ! -f /.env ]; then
    echo 'No .env file found. Exiting!'
    exit 1
fi
. /.env

wait-for-it -t 0 db:5432
./manage.py migrate

if [ $# = 0 ]; then
    ./manage.py collectstatic --noinput
    ./manage.py create_groups

    if [ "$DEBUG" -a "$DEBUG" != '0' ]; then
        # When DEBUG=True, if no user exists, create one
        if [ "$(./manage.py shell -c 'from tomato.models import TomatoUser; print("" if TomatoUser.objects.exists() else "1")')" = 1 ]; then
            DJANGO_SUPERUSER_PASSWORD=tomato ./manage.py createsuperuser --noinput --username tomato --email tomato@example.com
        fi
        exec ./manage.py runserver
    else

        if [ -z "$GUNICORN_WORKERS" ]; then
            # max of round(num_cpus * 1.5 + 1) and 4
            GUNICORN_WORKERS="$(python -c 'import multiprocessing as m; print(max(round(m.cpu_count() * 1.5 + 1), 4))')"
        fi

        exec gunicorn \
            $GUNICORN_ARGS \
            --forwarded-allow-ips '*' \
            -b 0.0.0.0:8000 \
            -w $GUNICORN_WORKERS \
            --capture-output \
            --access-logfile - \
        tomato.wsgi
    fi
else
    echo "Executing: $@"
    echo
    exec "$@"
fi
