#export COMPOSE_PROJECT_NAME=1 C=c1 N=1 API=8008 COMP=4104 NET=8101 CONS=5051;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml down
#export COMPOSE_PROJECT_NAME=2 C=c1 N=2 API=8009 COMP=4106 NET=8102 CONS=5052;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml down
#export COMPOSE_PROJECT_NAME=3 C=c1 N=3 API=8010 COMP=4107 NET=8103 CONS=5053;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml down
#export COMPOSE_PROJECT_NAME=4 C=c1 N=4 API=8011 COMP=4108 NET=8104 CONS=5054;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml up
#export COMPOSE_PROJECT_NAME=5 C=c1 N=5 API=8012 COMP=4109 NET=8105 CONS=5055;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml up
#export COMPOSE_PROJECT_NAME=6 C=c1 N=6 API=8013 COMP=4110 NET=8106 CONS=5056;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml up
# cluster 2
#export COMPOSE_PROJECT_NAME=21 C=c2 N=1 API=8208 COMP=4204 NET=8201 CONS=5251;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml down
#export COMPOSE_PROJECT_NAME=22 C=c2 N=2 API=8209 COMP=4206 NET=8202 CONS=5252;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml down
#export COMPOSE_PROJECT_NAME=23 C=c2 N=3 API=8210 COMP=4207 NET=8203 CONS=5253;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml down
# cluster 3
#export COMPOSE_PROJECT_NAME=31 C=c3 N=1 API=8308 COMP=4304 NET=8301 CONS=5351;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml down
#export COMPOSE_PROJECT_NAME=32 C=c3 N=2 API=8309 COMP=4306 NET=8302 CONS=5352;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml down
#export COMPOSE_PROJECT_NAME=33 C=c3 N=3 API=8310 COMP=4307 NET=8303 CONS=5353;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml down
# cluster 4
#export COMPOSE_PROJECT_NAME=41 C=c4 N=1 API=8408 COMP=4404 NET=8401 CONS=5451;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml down
#export COMPOSE_PROJECT_NAME=42 C=c4 N=2 API=8409 COMP=4406 NET=8402 CONS=5452;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml down
#export COMPOSE_PROJECT_NAME=43 C=c4 N=3 API=8410 COMP=4407 NET=8403 CONS=5453;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml down
# cluster 5
#export COMPOSE_PROJECT_NAME=51 C=c5 N=1 API=8508 COMP=4504 NET=8501 CONS=5551;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml down
#export COMPOSE_PROJECT_NAME=52 C=c5 N=2 API=8509 COMP=4506 NET=8502 CONS=5552;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml down
#export COMPOSE_PROJECT_NAME=53 C=c5 N=3 API=8510 COMP=4507 NET=8503 CONS=5553;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml down
# cluster 6
#export COMPOSE_PROJECT_NAME=61 C=c6 N=1 API=8608 COMP=4604 NET=8601 CONS=5651;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml down
#export COMPOSE_PROJECT_NAME=62 C=c6 N=2 API=8609 COMP=4606 NET=8602 CONS=5652;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml down
#export COMPOSE_PROJECT_NAME=63 C=c6 N=3 API=8610 COMP=4607 NET=8603 CONS=5653;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml down
mode="up -d"
peers6="1 2 3 4 5 6"
peers="1 2 3"
PEERS="91.216.211.46 validator-bgx-c2-1;91.216.211.46 validator-bgx-c3-1"
if [ $1 == 'G' ]; then GENESIS="Y";shift; else GENESIS="N"; fi
 
function upCluster1 {
  echo "upCluster1 $#"
  for node in $@;do
    echo "START $node"
    case $node in
        1)
          export COMPOSE_PROJECT_NAME=1 G=$GENESIS C=c1 N=1 API=8008 COMP=4104 NET=8101 CONS=5051;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml $mode
        ;;
        2)
          export COMPOSE_PROJECT_NAME=2 G=$GENESIS C=c1 N=2 API=8009 COMP=4106 NET=8102 CONS=5052;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml $mode
        ;;
        3)
          export COMPOSE_PROJECT_NAME=3 G=$GENESIS C=c1 N=3 API=8010 COMP=4107 NET=8103 CONS=5053;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml $mode
        ;;
        4)
          export COMPOSE_PROJECT_NAME=4 G=$GENESIS C=c1 N=4 API=8011 COMP=4108 NET=8104 CONS=5054;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml $mode
        ;;
        5)
          export COMPOSE_PROJECT_NAME=5 G=$GENESIS C=c1 N=5 API=8012 COMP=4109 NET=8105 CONS=5055;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml $mode
        ;;
        6)
          export COMPOSE_PROJECT_NAME=6 G=$GENESIS C=c1 N=6 API=8013 COMP=4110 NET=8106 CONS=5056;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml $mode
        ;;
        *)
          echo "Undefined peer into cluster."
        ;;
     esac
  done
}
function upCluster2 {
  echo "upCluster2 $#"
  for node in $@;do
    #echo "START $node"
    case $node in
        1)
          export COMPOSE_PROJECT_NAME=21 G=$GENESIS C=c2 N=1 API=8208 COMP=4204 NET=8201 CONS=5251;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml $mode
        ;;
        2)
          export COMPOSE_PROJECT_NAME=22 G=$GENESIS C=c2 N=2 API=8209 COMP=4206 NET=8202 CONS=5252;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml $mode
        ;;
        3)
          export COMPOSE_PROJECT_NAME=23 G=$GENESIS C=c2 N=3 API=8210 COMP=4207 NET=8203 CONS=5253;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml $mode
        ;;
        4)
          export COMPOSE_PROJECT_NAME=24 G=$GENESIS C=c2 N=4 API=8211 COMP=4208 NET=8204 CONS=5254;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml $mode
        ;;
        5)
          export COMPOSE_PROJECT_NAME=25 G=$GENESIS C=c2 N=5 API=8212 COMP=4209 NET=8205 CONS=5255;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml $mode
        ;;
        6)
          export COMPOSE_PROJECT_NAME=26 G=$GENESIS C=c2 N=6 API=8213 COMP=4210 NET=8206 CONS=5256;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml $mode
        ;;
        *)
          echo "Undefined peer into cluster."
        ;;
     esac
  done
}
function upCluster3 {
  echo "upCluster3 $#"
  for node in $@;do
    #echo "START $node"
    case $node in
        1)
          export COMPOSE_PROJECT_NAME=31 G=$GENESIS C=c3 N=1 API=8308 COMP=4304 NET=8301 CONS=5351;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml $mode
        ;;
        2)
          export COMPOSE_PROJECT_NAME=32 G=$GENESIS C=c3 N=2 API=8309 COMP=4306 NET=8302 CONS=5352;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml $mode
        ;;
        3)
          export COMPOSE_PROJECT_NAME=33 G=$GENESIS C=c3 N=3 API=8310 COMP=4307 NET=8303 CONS=5353;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml $mode
        ;;
        *)
          echo "Undefined peer into cluster."
        ;;
     esac
  done
}
function upCluster4 {
  echo "upCluster4 $#"
  for node in $@;do
    #echo "START $node"
    case $node in
        1)
          export COMPOSE_PROJECT_NAME=41 G=$GENESIS C=c4 N=1 API=8408 COMP=4404 NET=8401 CONS=5451;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml $mode
        ;;
        2)
          export COMPOSE_PROJECT_NAME=42 G=$GENESIS C=c4 N=2 API=8409 COMP=4406 NET=8402 CONS=5452;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml $mode
        ;;
        3)
          export COMPOSE_PROJECT_NAME=43 G=$GENESIS C=c4 N=3 API=8410 COMP=4407 NET=8403 CONS=5453;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml $mode
        ;;
        *)
          echo "Undefined peer into cluster."
        ;;
     esac
  done
}
function upCluster5 {
  echo "upCluster5 $#"
  for node in $@;do
    echo "START $node"
    case $node in
        1)
          export COMPOSE_PROJECT_NAME=51 G=$GENESIS C=c5 N=1 API=8508 COMP=4504 NET=8501 CONS=5551;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml $mode
        ;;
        2)
          export COMPOSE_PROJECT_NAME=52 G=$GENESIS C=c5 N=2 API=8509 COMP=4506 NET=8502 CONS=5552;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml $mode
        ;;
        3)
          export COMPOSE_PROJECT_NAME=53 G=$GENESIS C=c5 N=3 API=8510 COMP=4507 NET=8503 CONS=5553;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml $mode
        ;;
        *)
          echo "Undefined peer into cluster."
        ;;
     esac
  done
}
function upCluster6 {
  echo "upCluster6 $#"
  for node in $@;do
    echo "START $node"
    case $node in
        1)
          export COMPOSE_PROJECT_NAME=61 G=$GENESIS C=c6 N=1 API=8608 COMP=4604 NET=8601 CONS=5651;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml $mode
        ;;
        2)
          export COMPOSE_PROJECT_NAME=62 G=$GENESIS C=c6 N=2 API=8609 COMP=4606 NET=8602 CONS=5652;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml $mode
        ;;
        3)
          export COMPOSE_PROJECT_NAME=63 G=$GENESIS C=c6 N=3 API=8610 COMP=4607 NET=8603 CONS=5653;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml $mode
        ;;
        *)
          echo "Undefined peer into cluster."
        ;;
     esac
  done
}
cluster=$1
shift
case $cluster in
     1|genesis)
          echo "Start cluster genesis"
          if (( $# > 0 ));then
            upCluster1 $@
          else  
            upCluster1 $peers
          fi
          ;;
     2)
          echo "Start cluster 2"
          if (( $# > 0 ));then
            upCluster2 $@
          else  
            upCluster2 $peers
          fi 
          ;;
     3)
          echo "Start cluster 3"
          if (( $# > 0 ));then
            upCluster3 $@
          else  
            upCluster3 $peers
          fi
          ;; 
     4)
          echo "Start cluster 4"
          if (( $# > 0 ));then
            upCluster4 $@
          else  
            upCluster4 $peers
          fi 
          ;; 
     5)
          echo "Start cluster 5"
          if (( $# > 0 ));then
            upCluster5 $@
          else  
            upCluster5 $peers
          fi
          ;; 
     6)
          echo "Start cluster 6"
          if (( $# > 0 ));then
            upCluster6 $@
          else  
            upCluster6 $peers
          fi
          
          ;; 
     all)
          upCluster1 $peers
          upCluster2 $peers
          upCluster3 $peers
          upCluster4 $peers
          upCluster5 $peers
          upCluster6 $peers
          ;;  
     *)
          echo "Enter cluster number or all."
          ;;
esac


