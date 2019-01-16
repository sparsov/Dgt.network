#! /bin/sh
DAEMON_ARGS="-d"
FROM="/home/bgx/Projects/bgx"
#
# Function that start dashboard
#
(cd $FROM;ls -l;docker-compose -f bgx/docker/docker-compose-dashboard-bgx.yaml up $DAEMON_ARGS)

