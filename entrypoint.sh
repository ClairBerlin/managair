#!/bin/sh

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

exec "$@"