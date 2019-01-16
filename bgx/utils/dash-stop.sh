#! /bin/sh
FROM="/home/bgx/Projects/bgx"
FROM1="/home/hyper/Hyperledger/bgx"
#
# Function that start dashboard
#
(cd $FROM;docker-compose -f bgx/docker/docker-compose-dashboard-bgx.yaml down)

