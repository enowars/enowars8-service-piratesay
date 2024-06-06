#!/bin/sh
set -e
set -x

# Chown the mounted data volume
chown -R service:service "/data/"

# Force the deletion script to run once
/usr/local/bin/delete_old_files.sh

# Start cron service
service cron start

# Build the project
make

# Launch our service as user 'service' and run 'run' within gdb
# exec su -s /bin/sh -c 'gdb -ex "set follow-fork-mode child" -ex run -ex quit piratesay' service
exec su -s /bin/sh -c './piratesay' service

# Keep the container running
# tail -f /dev/null
