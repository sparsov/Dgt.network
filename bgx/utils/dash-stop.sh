#! /bin/sh
FROM="/home/bgx/Projects/bgx"
#
# Function that start dashboard
#
(cd $FROM;docker-compose -f bgx/docker/docker-compose-dashboard-bgx.yaml down)

