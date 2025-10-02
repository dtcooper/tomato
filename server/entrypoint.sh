#!/bin/sh


cd "$(dirname "$0")"

if [ ! -f /.env ]; then
    echo 'No .env file found. Exiting!'
    exit 1
fi
. /.env

NO_SECRET_KEY=
if [ -z "$SECRET_KEY" ]; then
    NO_SECRET_KEY=1
fi

if [ -z "$__SKIP_CHECKS" ]; then
    wait-for-it --timeout 0 --service db:5432 --service redis:6379
fi

# If we're not running huey, migration and create tomato:tomato user when DEBUG=1
if [ -z "$__RUN_HUEY" -a -z "$__RUN_API" -a -z "$__SKIP_CHECKS" ]; then
    if [ "$NO_SECRET_KEY" ]; then
        echo 'Generating SECRET_KEY...'
        NEW_SECRET_KEY="$(python -c 'import string as s, random as r; print("".join(r.choice(s.ascii_letters + s.digits) for _ in range(54)))')"
        sed "s/^SECRET_KEY=/SECRET_KEY=$NEW_SECRET_KEY/" /.env > /tmp/new-env
        cp /tmp/new-env /.env
        rm /tmp/new-env
        . /.env
    fi

    ./manage.py createcachetable -v0
    ./manage.py migrate
    if [ "$DEBUG" -a "$DEBUG" != '0' ]; then
        if [ "$(./manage.py shell -v 0 -c 'from tomato.models import User; print("" if User.objects.exists() else "1")')" = 1 ]; then
            DJANGO_SUPERUSER_PASSWORD=tomato ./manage.py createsuperuser --noinput --username tomato
        fi

        if [ ! -d 'tomato/static/vendor/node_modules' ]; then
            echo "Installing vendor node modules..."
            cd tomato/static/vendor
            npm install
            cd "$(dirname "$0")"
        fi
    fi

elif [ "$NO_SECRET_KEY" ]; then
    echo 'Delaying huey/api while SECRET_KEY is being generated...'
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

    elif [ "$__RUN_API" ]; then
        if [ -z "$DEBUG" -o "$DEBUG" = '0' ]; then
            echo 'Delaying api startup for 10 seconds...'
            sleep 10
        fi
        exec python api
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
