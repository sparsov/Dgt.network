# only validator
#docker network disconnect bgx-network sawtooth-shell-bgx-2
#docker network disconnect bgx2-network sawtooth-shell-bgx
# peer1 - peer2
docker network disconnect bgx2-network validator-bgx-1
docker network disconnect bgx1-network validator-bgx-2
# peer1 - peer3
docker network disconnect bgx3-network validator-bgx-1
docker network disconnect bgx1-network validator-bgx-3
# peer1 - peer4
docker network disconnect bgx4-network validator-bgx-1
docker network disconnect bgx1-network validator-bgx-4
# peer1 - peer5
docker network disconnect bgx5-network validator-bgx-1
docker network disconnect bgx1-network validator-bgx-5
#peer2 - peer3
docker network disconnect bgx2-network validator-bgx-3
docker network disconnect bgx3-network validator-bgx-2
#peer2 - peer4
docker network disconnect bgx2-network validator-bgx-4
docker network disconnect bgx4-network validator-bgx-2
#peer2 - peer5
docker network disconnect bgx2-network validator-bgx-5
docker network disconnect bgx5-network validator-bgx-2
# peer3 - peer4
docker network disconnect bgx4-network validator-bgx-3
docker network disconnect bgx3-network validator-bgx-4 
# peer3 - peer5
docker network disconnect bgx5-network validator-bgx-3
docker network disconnect bgx3-network validator-bgx-5
# peer4 -peer5
docker network disconnect bgx5-network validator-bgx-4
docker network disconnect bgx4-network validator-bgx-5
