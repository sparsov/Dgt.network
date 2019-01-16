#! /bin/sh
DAEMON_ARGS="-d"
FROM="/home/bgx/Projects/bgx"
FROM1="/home/hyper/Hyperledger/bgx"
#
# Function that starts the daemon/service
#
(cd $FROM;ls -l;docker-compose -f bgx/docker/docker-compose-netall-reg-dev-loc.yaml up $DAEMON_ARGS)

