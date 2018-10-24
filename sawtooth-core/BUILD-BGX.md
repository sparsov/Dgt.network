To build the requirements to run a validator network, run this command
$ docker-compose -f docker-compose-bgx.yaml build

Also provided is a docker-compose file which builds a full set of images
with Sawtooth installed, and only the run-time dependencies installed.
$ docker-compose -f docker-compose-installed-bgx.yaml build

To run a full validator node from the local source:
$ docker-compose -f docker-compose-net-pbft.yaml up
