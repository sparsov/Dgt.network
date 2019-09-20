#docker network connect bgx-network sawtooth-shell-bgx-2
#docker network connect bgx2-network sawtooth-shell-bgx
#docker network connect bgx-network sawtooth-shell-bgx-3
#docker network connect bgx3-network sawtooth-shell-bgx
#peer + peer2
docker network connect bgx2-network validator-nbgx
docker network connect bgx-network validator-nbgx-2
# peer + peer3
docker network connect bgx3-network validator-nbgx
docker network connect bgx-network validator-nbgx-3
#peer2 + peer3
docker network connect bgx2-network validator-nbgx-3
docker network connect bgx3-network validator-nbgx-2
#peer + peer4
docker network connect bgx4-network validator-nbgx
docker network connect bgx-network validator-nbgx-4
# peer2 + peer4
docker network connect bgx2-network validator-nbgx-4
docker network connect bgx4-network validator-nbgx-2
# peer3 + peer4
docker network connect bgx4-network validator-nbgx-3
docker network connect bgx3-network validator-nbgx-4
