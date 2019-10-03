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
$ docker exec -it shell-bgx-1 bash
For list created tokens run into shell-bgx. 
$ smart-bgt list  --url http://rest-api:8009
# not in sawtooth shell
$ curl http://localhost:8008/blocks
# smart-bgt init BGX_Token 21fad1db7c1e4f3fb98bb16fcff6942b4b2b9f890196b8754399ebfd74718de1 0xFB2F7C8687F6d86a031D2DE3d51f4c62e83AdA22 20 1 1 --url http://bgx-api-1:8008
# smart-bgt transfer 0236bd0b2f6041338ffe5a2236be89f369ec3094e5247bb40aad3aaa18ff2da395 222 0.1 --url http://rest-api:8008 

# start REST-API 
$ docker-compose -f bgx/docker/docker-compose-rest-api.yaml up 
# make transfer 
$ cd bgs/utils
$ bash transfer.sh 673fcacfb51214e0543b786da79956b541e7d792 4aa37a37b9793a7f3696129d9a367b26fd0b2b1c 1
# create wallet
$ bash create_wallet.sh 673fcacfb51214e0543b786da79956b541e7d792
# get wallet
$ bash get_wallet.sh 673fcacfb51214e0543b786da79956b541e7d792
smart-bgt init BGX_Token 21fad1db7c1e4f3fb98bb16fcff6942b4b2b9f890196b8754399ebfd74718de1 0xFB2F7C8687F6d86a031D2DE3d51f4c62e83AdA22 2000000 1 1 --url http://bgx-api:8018
smart-bgt transfer 0236bd0b2f6041338ffe5a2236be89f369ec3094e5247bb40aad3aaa18ff2da395 028c7e06db3af50a9958390e3e29f166b1cf6198586acf37cde46c8ea54e4a79ea 30 any --url bgx-api:8018
# use orient
docker-compose -f bgx/docker/docker-compose-net-odb-dev-loc.yaml up
# user validator without rust
docker-compose -f bgx/docker/docker-compose-net-bgx-val-pbft.yaml up
# docker-compose -f bgx/docker/docker-compose-net-bgx-val-pbft.yaml 

# for console
#bgx dag show val --url http://bgx-api-2:8009;echo ---;bgx dag show nest --url http://bgx-api-2:8009 -Fjson
#bgx dag show integrity --url http://bgx-api-1:8008;bgx dag show integrity --url http://bgx-api-2:8009
#bgx block list --url http://bgx-api-1:8008;bgx block list --url http://bgx-api-2:8009
#bgt workload --rate 11 -d 5 --url http://bgx-api-1:8008

# dash
docker-compose -f bgx/docker/docker-compose-dashboard-bgx.yaml up
docker-compose -f bgx/docker/docker-compose-dashboard-bgx2.yaml up
#

# valid
docker-compose -f bgx/docker/docker-compose-net-bgx-val-pbft.yaml up
docker-compose -f bgx/docker/docker-compose-net2-bgx-val-pbft.yaml up
# nodes
export COMPOSE_PROJECT_NAME=1 N=1 API=8008 COMP=4004 NET=8800 CONS=5050;docker-compose -f bgx/docker/docker-compose-netN-bgx-val-pbft.yaml up
export COMPOSE_PROJECT_NAME=2 N=2 API=8009 COMP=4006 NET=8801 CONS=5051;docker-compose -f bgx/docker/docker-compose-netN-bgx-val-pbft.yaml up
export COMPOSE_PROJECT_NAME=3 N=3 API=8010 COMP=4007 NET=8802 CONS=5052;docker-compose -f bgx/docker/docker-compose-netN-bgx-val-pbft.yaml up
export COMPOSE_PROJECT_NAME=4 N=4 API=8011 COMP=4008 NET=8803 CONS=5053;docker-compose -f bgx/docker/docker-compose-netN-bgx-val-pbft.yaml up
export COMPOSE_PROJECT_NAME=5 N=5 API=8012 COMP=4009 NET=8804 CONS=5054;docker-compose -f bgx/docker/docker-compose-netN-bgx-val-pbft.yaml up
export COMPOSE_PROJECT_NAME=6 N=6 API=8013 COMP=4010 NET=8805 CONS=5055;docker-compose -f bgx/docker/docker-compose-netN-bgx-val-pbft.yaml up

