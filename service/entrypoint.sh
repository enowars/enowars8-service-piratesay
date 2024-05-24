#!/bin/sh
set -e
set -x

# Chown the mounted data volume
chown -R service:service "/data/"

# Build the project
make

# Launch our service as user 'service' and run 'run' within gdb
exec su -s /bin/sh -c 'gdb -ex run -ex quit pirateprattle' service
