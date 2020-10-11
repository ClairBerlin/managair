#!/bin/sh

echo "Preloading test data...\n"
echo "\nUser and permissions..."
docker exec -it managair_server python3 manage.py loaddata user_manager/fixtures/user-fixtures.json
echo "\nDevices..."
docker exec -it managair_server python3 manage.py loaddata device_manager/fixtures/device-fixtures.json
echo "\nSamples..."
docker exec -it managair_server python3 manage.py loaddata ts_manager/fixtures/data-fixtures.json
echo "\nSites..."
docker exec -it managair_server python3 manage.py loaddata site_manager/fixtures/site-fixtures.json
echo "\nDone!"
