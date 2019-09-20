# only validator
#docker network disconnect bgx-network sawtooth-shell-bgx-2
#docker network disconnect bgx2-network sawtooth-shell-bgx
# peer peer2
docker network disconnect bgx2-network validator-nbgx
docker network disconnect bgx-network validator-nbgx-2
# peer - peer3
docker network disconnect bgx3-network validator-nbgx
docker network disconnect bgx-network validator-nbgx-3
# peer - peer4
docker network disconnect bgx4-network validator-nbgx
docker network disconnect bgx-network validator-nbgx-4
#peer2 - peer3
docker network disconnect bgx2-network validator-nbgx-3
docker network disconnect bgx3-network validator-nbgx-2
#peer2 - peer4
docker network disconnect bgx2-network validator-nbgx-4
docker network disconnect bgx4-network validator-nbgx-2
# peer3 - peer4
docker network disconnect bgx4-network validator-nbgx-3
docker network disconnect bgx3-network validator-nbgx-4 
