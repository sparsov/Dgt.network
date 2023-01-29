bash upDecCluster.sh -G -SC -CB openssl 1 1
bash upDgtNotary.sh -CB openssl 1
bash upDgtNotary.sh -CB openssl -NR 2
docker exec -it shell-dgt-c1-1 bash
docker exec -it vault-n2 bash
