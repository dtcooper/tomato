#!/bin/sh

if [ ! -f /.env ]; then
    echo 'No .env file found. Exiting!'
    exit 1
fi
. /.env

wait-for-it -t 0 db:5432
./manage.py migrate

if [ "$DEBUG" -a "$DEBUG" != '0' ]; then
    # When DEBUG=True, if no user exists, create one with tomato:tomato
    if [ "$(./manage.py shell -c 'from tomato.models import User; print("" if User.objects.exists() else "1")')" = 1 ]; then
        DJANGO_SUPERUSER_PASSWORD=tomato ./manage.py createsuperuser --noinput --username tomato --email tomato@example.com
    fi

    # Make psql/redis work easily
    export PGHOST=db
    export PGUSER=postgres
    export PGPASSWORD=postgres
fi

if [ $# = 0 ]; then
    if [ "$DEBUG" -a "$DEBUG" != '0' ]; then

        exec ./manage.py runserver
    else
        ./manage.py collectstatic --noinput

        if [ -z "$GUNICORN_WORKERS" ]; then
            # num_cpus * 2 + 1 workers
            GUNICORN_WORKERS="$(python -c 'import multiprocessing as m; print(m.cpu_count() * 2 + 1)')"
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
