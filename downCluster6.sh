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
mode=down
peers="1 2 3"
peers6="1 2 3 4 5 6"
function downCluster1 {
  echo "downCluster3 $#"
  for node in $@;do
    echo "START $node"
    case $node in
        1)
          export COMPOSE_PROJECT_NAME=1 C=c1 N=1 API=8008 COMP=4104 NET=8101 CONS=5051;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml $mode
        ;;
        2)
          export COMPOSE_PROJECT_NAME=2 C=c1 N=2 API=8009 COMP=4106 NET=8102 CONS=5052;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml $mode
        ;;
        3)
          export COMPOSE_PROJECT_NAME=3 C=c1 N=3 API=8010 COMP=4107 NET=8103 CONS=5053;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml $mode
        ;;
        4)
          export COMPOSE_PROJECT_NAME=4 C=c1 N=4 API=8011 COMP=4108 NET=8104 CONS=5054;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml $mode
        ;;
        5)
          export COMPOSE_PROJECT_NAME=5 C=c1 N=5 API=8012 COMP=4109 NET=8105 CONS=5055;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml $mode
        ;;
        6)
          export COMPOSE_PROJECT_NAME=6 C=c1 N=6 API=8013 COMP=4110 NET=8106 CONS=5056;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml $mode
        ;;
        *)
          echo "Undefined peer into cluster."
        ;;
     esac
  done
}
function downCluster2 {
  echo "downCluster3 $#"
  for node in $@;do
    #echo "START $node"
    case $node in
        1)
          export COMPOSE_PROJECT_NAME=21 C=c2 N=1 API=8208 COMP=4204 NET=8201 CONS=5251;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml $mode
        ;;
        2)
          export COMPOSE_PROJECT_NAME=22 C=c2 N=2 API=8209 COMP=4206 NET=8202 CONS=5252;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml $mode
        ;;
        3)
          export COMPOSE_PROJECT_NAME=23 C=c2 N=3 API=8210 COMP=4207 NET=8203 CONS=5253;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml $mode
        ;;
        4)
          export COMPOSE_PROJECT_NAME=24 C=c2 N=4 API=8211 COMP=4208 NET=8204 CONS=5254;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml $mode
        ;;
        5)
          export COMPOSE_PROJECT_NAME=25 C=c2 N=5 API=8212 COMP=4209 NET=8205 CONS=5255;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml $mode
        ;;
        6)
          export COMPOSE_PROJECT_NAME=26 C=c2 N=6 API=8213 COMP=4210 NET=8206 CONS=5256;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml $mode
        ;;
        *)
          echo "Undefined peer into cluster."
        ;;
     esac
  done
}
function downCluster3 {
  echo "downCluster3 $#"
  for node in $@;do
    #echo "START $node"
    case $node in
        1)
          export COMPOSE_PROJECT_NAME=31 C=c3 N=1 API=8308 COMP=4304 NET=8301 CONS=5351;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml $mode
        ;;
        2)
          export COMPOSE_PROJECT_NAME=32 C=c3 N=2 API=8309 COMP=4306 NET=8302 CONS=5352;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml $mode
        ;;
        3)
          export COMPOSE_PROJECT_NAME=33 C=c3 N=3 API=8310 COMP=4307 NET=8303 CONS=5353;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml $mode
        ;;
        4)
          export COMPOSE_PROJECT_NAME=34 C=c3 N=4 API=8311 COMP=4308 NET=8304 CONS=5354;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml $mode
        ;;
        5)
          export COMPOSE_PROJECT_NAME=35 C=c3 N=5 API=8312 COMP=4309 NET=8305 CONS=5355;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml $mode
        ;;
        6)
          export COMPOSE_PROJECT_NAME=36 C=c3 N=6 API=8313 COMP=4310 NET=8306 CONS=5356;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml $mode
        ;;
        7)
          export COMPOSE_PROJECT_NAME=37 C=c3 N=7 API=8314 COMP=4311 NET=8307 CONS=5357;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml $mode
        ;;
        *)
          echo "Undefined peer into cluster."
        ;;
     esac
  done
}
function downCluster4 {
  echo "downCluster4 $#"
  for node in $@;do
    #echo "START $node"
    case $node in
        1)
          export COMPOSE_PROJECT_NAME=41 C=c4 N=1 API=8408 COMP=4404 NET=8401 CONS=5451;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml $mode
        ;;
        2)
          export COMPOSE_PROJECT_NAME=42 C=c4 N=2 API=8409 COMP=4406 NET=8402 CONS=5452;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml $mode
        ;;
        3)
          export COMPOSE_PROJECT_NAME=43 C=c4 N=3 API=8410 COMP=4407 NET=8403 CONS=5453;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml $mode
        ;;
        4)
          export COMPOSE_PROJECT_NAME=44 C=c4 N=4 API=8411 COMP=4408 NET=8404 CONS=5454;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml $mode
        ;;
        5)
          export COMPOSE_PROJECT_NAME=45 C=c4 N=5 API=8412 COMP=4409 NET=8405 CONS=5455;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml $mode
        ;;
        6)
          export COMPOSE_PROJECT_NAME=46 C=c4 N=6 API=8413 COMP=4410 NET=8406 CONS=5456;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml $mode
        ;;
        *)
          echo "Undefined peer into cluster."
        ;;
     esac
  done
}
function downCluster5 {
  echo "downCluster5 $#"
  for node in $@;do
    echo "START $node"
    case $node in
        1)
          export COMPOSE_PROJECT_NAME=51 C=c5 N=1 API=8508 COMP=4504 NET=8501 CONS=5551;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml $mode
        ;;
        2)
          export COMPOSE_PROJECT_NAME=52 C=c5 N=2 API=8509 COMP=4506 NET=8502 CONS=5552;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml $mode
        ;;
        3)
          export COMPOSE_PROJECT_NAME=53 C=c5 N=3 API=8510 COMP=4507 NET=8503 CONS=5553;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml $mode
        ;;
        4)
          export COMPOSE_PROJECT_NAME=54 C=c5 N=4 API=8511 COMP=4508 NET=8504 CONS=5554;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml $mode
        ;;
        5)
          export COMPOSE_PROJECT_NAME=55 C=c5 N=5 API=8512 COMP=4509 NET=8505 CONS=5555;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml $mode
        ;;
        6)
          export COMPOSE_PROJECT_NAME=56 C=c5 N=6 API=8513 COMP=4510 NET=8506 CONS=5556;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml $mode
        ;;
        *)
          echo "Undefined peer into cluster."
        ;;
     esac
  done
}
function downCluster6 {
  echo "downCluster6 $#"
  for node in $@;do
    echo "START $node"
    case $node in
        1)
          export COMPOSE_PROJECT_NAME=61 C=c6 N=1 API=8608 COMP=4604 NET=8601 CONS=5651;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml $mode
        ;;
        2)
          export COMPOSE_PROJECT_NAME=62 C=c6 N=2 API=8609 COMP=4606 NET=8602 CONS=5652;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml $mode
        ;;
        3)
          export COMPOSE_PROJECT_NAME=63 C=c6 N=3 API=8610 COMP=4607 NET=8603 CONS=5653;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml $mode
        ;;
        4)
          export COMPOSE_PROJECT_NAME=64 C=c6 N=4 API=8611 COMP=4608 NET=8604 CONS=5654;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml $mode
        ;;
        5)
          export COMPOSE_PROJECT_NAME=65 C=c6 N=5 API=8612 COMP=4609 NET=8605 CONS=5655;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml $mode
        ;;
        6)
          export COMPOSE_PROJECT_NAME=66 C=c6 N=6 API=8613 COMP=4610 NET=8606 CONS=5656;docker-compose -f bgx/docker/docker-compose-netCN-bgx-val-pbft.yaml $mode
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
            downCluster1 $@
          else  
            downCluster1 $peers6 
          fi
          ;;
     2)
          echo "Start cluster 2"
          if (( $# > 0 ));then
            downCluster2 $@
          else  
            downCluster2 $peers6
          fi 
          ;;
     3)
          echo "Start cluster 3"
          if (( $# > 0 ));then
            downCluster3 $@
          else  
            downCluster3 $peers6
          fi
          ;; 
     4)
          echo "Start cluster 4"
          if (( $# > 0 ));then
            downCluster4 $@
          else  
            downCluster4 $peers6
          fi 
          ;; 
     5)
          echo "Start cluster 5"
          if (( $# > 0 ));then
            downCluster5 $@
          else  
            downCluster5 $peers6
          fi
          ;; 
     6)
          echo "Start cluster 6"
          if (( $# > 0 ));then
            downCluster6 $@
          else  
            downCluster6 $peers6 
          fi
          
          ;;
     all)
          downCluster1 $peers6
          downCluster2 $peers6
          downCluster3 $peers6
          downCluster4 $peers6
          downCluster5 $peers6
          downCluster6 $peers6 
          ;;   
     *)
          echo "Enter cluster number."
          ;;
esac

