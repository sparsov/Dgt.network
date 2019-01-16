#! /bin/sh
DAEMON_ARGS="-d"
FROM="/home/bgx/Projects/bgx"
FROM1=""
(cd $FROM;docker-compose -f bgx/docker/docker-compose-netall-reg-dev-loc.yaml down)

