#!/bin/sh

if [ ! -f /.env ]; then
    echo 'No .env file found. Exiting!'
    exit 1
fi
. /.env

NO_SECRET_KEY=
if [ -z "$SECRET_KEY" ]; then
    NO_SECRET_KEY=1
fi

wait-for-it --timeout 0 --service db:5432 --service redis:6379

# If we're not running huey, migration and create tomato:tomato when DEBUG=1
if [ -z "$__RUN_HUEY" ]; then
    if [ "$NO_SECRET_KEY" ]; then
        echo 'Generating SECRET_KEY...'
        python -c 'import base62 as b, dotenv as d, secrets as s; d.set_key("/.env", "SECRET_KEY", b.encodebytes(s.token_bytes(40)))'
        . /.env
    fi

    ./manage.py migrate
    if [ "$DEBUG" -a "$DEBUG" != '0' ]; then
        if [ "$(./manage.py shell -c 'from tomato.models import User; print("" if User.objects.exists() else "1")')" = 1 ]; then
            DJANGO_SUPERUSER_PASSWORD=tomato ./manage.py createsuperuser --noinput --username tomato
        fi
    fi

elif [ "$NO_SECRET_KEY" ]; then
    echo 'Delaying huey while SECRET_KEY is being generated...'
    sleep 10
    . /.env
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
            NUM_HUEY_WORKERS="$(python -c 'import multiprocessing as m; print(m.cpu_count() * 3 + 1)')"
        fi
        CMD="./manage.py run_huey --workers $NUM_HUEY_WORKERS --flush-locks"
        if [ "$DEBUG" -a "$DEBUG" != '0' ]; then
            exec watchmedo auto-restart --directory=./ --pattern=*.py --recursive -- $CMD
        else
            echo 'Delaying huey startup for 10 seconds...'
            sleep 10
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
    if [ -z "$__SILENT" ]; then
        echo "Executing: $@"
        echo
    fi
    exec "$@"
fi
