#!/bin/sh
set -e
set -x

# Chown the mounted data volume
chown -R service:service "/data/"

# Create the necessary directories
./create_directories.sh

# Force the deletion script to run once using a relative path
./delete_old_files.sh

# Start cron service
cron

# Launch our service as user 'service'
exec su -s /bin/sh -c '/src/piratesay' service