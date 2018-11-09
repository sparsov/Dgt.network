![Sawtooth=BGX](bgx/images/logo-bgx.png)

Hyperledger Sawtooth-BGX
-------------

Hyperledger Sawtooth-BGX is an enterprise solution for building, deploying, and
running distributed ledgers (also called blockchains). It provides an extremely
modular and flexible platform for implementing transaction-based updates to
shared state between untrusted parties coordinated by consensus algorithms.

.
To build the requirements to run a validator network, run this command
$ docker-compose -f bgx/docker/docker-compose-bgx.yaml build

Also provided is a docker-compose file which builds a full set of images
with Sawtooth-BGX installed, and only the run-time dependencies installed.

$ docker-compose -f bgx/docker/docker-compose-installed-bgx.yaml build validator

To run a full validator node from the local source.
$ docker-compose -f bgx/docker/docker-compose-net-bgx.yaml up

For running shell-bgx run next bash cmd .
$ docker exec -it sawtooth-shell-bgx bash
For list created tokens run into shell-bgx. 
$ smart-bgt list  --url http://rest-api:8009
