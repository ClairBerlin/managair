#!/bin/bash

if [ "$DATABASE" = "postgresql" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $SQL_HOST $SQL_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi

doMigrate=${DB_MIGRATE:-false}
if [ "$doMigrate" = true ] ;
then
  python manage.py migrate
fi

doCollectStaticFiles=${COLLECT_STATIC_FILES:-false}
if [ "$doCollectStaticFiles" = true ] ;
then
  python manage.py collectstatic --noinput
fi

exec "$@"
