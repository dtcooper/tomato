#!/bin/sh

if [ ! -f /.env ]; then
    echo 'No .env file found. Exiting!'
    exit 1
fi
. /.env

wait-for-it -t 0 db:5432
wait-for-it -t 0 redis:6379

# If we're not running huey, migration and create tomato:tomato when DEBUG=1
if [ -z "$__RUN_HUEY" ]; then
    ./manage.py migrate
    if [ "$DEBUG" -a "$DEBUG" != '0' ]; then
        if [ "$(./manage.py shell -c 'from tomato.models import User; print("" if User.objects.exists() else "1")')" = 1 ]; then
            DJANGO_SUPERUSER_PASSWORD=tomato ./manage.py createsuperuser --noinput --username tomato --email tomato@example.com
        fi
    fi
fi

if [ "$DEBUG" -a "$DEBUG" != '0' ]; then
    export PGHOST=db
    export PGUSER=postgres
    export PGPASSWORD=postgres
fi

if [ $# = 0 ]; then
    if [ "$__RUN_HUEY" ]; then
        if [ -z "$NUM_HUEY_WORKERS" ]; then
            #  num_cpus * 4 + 2
            NUM_HUEY_WORKERS="$(python -c 'import multiprocessing as m; print(m.cpu_count() * 4 + 2)')"
        fi
        CMD="./manage.py run_huey --workers $NUM_HUEY_WORKERS --flush-locks"
        if [ "$DEBUG" -a "$DEBUG" != '0' ]; then
            exec watchmedo auto-restart --directory=./ --pattern=*.py --recursive -- $CMD
        else
            exec $CMD
        fi

    else
        if [ "$DEBUG" -a "$DEBUG" != '0' ]; then
            exec ./manage.py runserver

        else
            ./manage.py collectstatic --noinput

            if [ -z "$NUM_GUNICORN_WORKERS" ]; then
                # num_cpus * 2 + 1 workers
                NUM_GUNICORN_WORKERS="$(python -c 'import multiprocessing as m; print(m.cpu_count() * 2 + 1)')"
            fi

            exec gunicorn \
                $GUNICORN_ARGS \
                --forwarded-allow-ips '*' \
                -b 0.0.0.0:8000 \
                -w $NUM_GUNICORN_WORKERS \
                --capture-output \
                --access-logfile - \
            tomato.wsgi
        fi
    fi
else
    echo "Executing: $@"
    echo
    exec "$@"
fi
