To build the requirements to run a validator network, run this command
$ docker-compose -f bgx/docker/docker-compose-bgx.yaml build

Also provided is a docker-compose file which builds a full set of images
with Sawtooth installed, and only the run-time dependencies installed.
$ docker-compose -f bgx/docker/docker-compose-installed-bgx.yaml build validator

To run a full validator node from the local source:
$ docker-compose -f bgx/docker/docker-compose-net-bgx.yaml up
