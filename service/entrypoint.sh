#!/bin/sh
set -e
set -x

# Chown the mounted data volume
chown -R service:service "/data/"

# Build the project
make

# Launch our service as user 'service'
exec su -s /bin/sh -c './pirateprattle' service