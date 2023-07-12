#!/bin/bash
# DGT SERVICE CONTROL
#
source ./.env.dgt
FILE_ENV=./.env.dgt
COMPOSE=docker-compose
SNM=$1
shift
if ! command -v $COMPOSE &> /dev/null
then
    echo "$COMPOSE could not be found"
    echo "Use docker with option compose"
    COMPOSE="docker compose"
fi
#FCOMPOSE="docker-compose-netCN-dgt-dec-ci.yaml"
#DGT_PARAM_LIST=${DGT_PARAMS[@]} #(PEER CLUST NODE GENESIS SINGLE PCONTROL PEERING NETWORK METRIC SIGNED INFLUXDB DBHOST DBUSER DBPASS PNM KYC CRYPTO_BACK HTTPS_MODE ACCESS_TOKEN)
PEER_PARAMS=()
PEER_LIST=()
LNAME=

NPROTO="prototype"
delim=' '
CBLUE="\033[0m\033[36m"
CRED="\033[0m\033[31m"
CDEF="\033[0m"


function setPeerType {
  if [[ $SNM == "dash"* ]]; then
            PEER_LIST=${DASH_LIST[@]}
            LNAME=DASH_LIST
            PEER_PARAMS=${DGT_DASH_PARAMS[@]}

  elif  [[ " ${CLUSTER_LIST[@]} " == *" $SNM "* ]] || [[ $SNM == "dgt"* ]] ; then
           PEER_LIST=${CLUSTER_LIST[@]}
           LNAME=CLUSTER_LIST
           PEER_PARAMS=${DGT_PARAMS[@]}
  else 
        PEER_PARAMS=()
        echo -e $CRED "NO SUCH TYPE PEER." $CDEF
  fi

}
setPeerType
#echo "'$LNAME' '${PEER_LIST[@]}' ${PEER_PARAMS[@]} "


function doDashCompose {
   echo "doDashCompose $@"
   if test -f $DASH_FCOMP; then 
       eval PEER=\$PEER_${SNM^^}                                              
                                                           
       eval CLUST=\$CLUST_${SNM^^}                                                
       eval NODE=\$NODE_${SNM^^}                                                
       eval SIGNED=\$SIGNED_${SNM^^}
       eval PNM=\$PNM_${SNM^^}
       eval CRYPTO_BACK=\$CRYPTO_BACK_${SNM^^}
       eval HTTPS_MODE=\$HTTPS_MODE_${SNM^^}
       eval ACCESS_TOKEN=\$ACCESS_TOKEN_${SNM^^}
       eval API=\$API_${SNM^^}
       eval COMP=\$COMP_${SNM^^}

                                             
 
        #export COMPOSE_PROJECT_NAME=1 G=$GENESIS C=c1 N=1 API=8108 COMP=4104 NET=8101 CONS=5051;docker-compose -f docker/$FCOMPOSE $mode
        export COMPOSE_PROJECT_NAME=$SNM C=$CLUST N=$NODE API=$API COMP=$COMP  \
               SIGNED=$SIGNED  \
               PNM=$PNM CRYPTO_BACK=$CRYPTO_BACK KYC=$KYC HTTPS_MODE=$HTTPS_MODE; \
               $COMPOSE -f $DASH_FCOMP $CMD $@;                           
       
   else                                                                              
       echo -e $CRED "Create and add $DASH_FCOMP"   $CDEF                      
   fi

}

function doDgtCompose {
   eval PEER=\$PEER_${SNM^^}
   if [ -z ${PEER} ] ;then                                                            
      echo -e $CRED "UNDEFINED DGT PEER '$SNM'" $CDEF                              
      return                                                                                        
   fi

   echo -e $CBLUE "$CMD service $SNM"  $CDEF
   if [[ $SNM == "dash"* ]]; then
        doDashCompose $@
        return
   fi
   if test -f $FCOMPOSE; then 
       eval PEER=\$PEER_${SNM^^}                                              
       eval CLUST=\$CLUST_${SNM^^}                                                
       eval NODE=\$NODE_${SNM^^}                                                
       eval GENESIS=\$GENESIS_${SNM^^}                                           
       eval SINGLE=\$SINGLE_${SNM^^}
       eval PCONTROL=\$PCONTROL_${SNM^^} 
       eval PEERING=\$PEERING_${SNM^^} 
       eval NETWORK=\$NETWORK_${SNM^^}                                           
       eval METRIC=\$METRIC_${SNM^^}
       eval SIGNED=\$SIGNED_${SNM^^}
       eval INFLUXDB=\$INFLUXDB_${SNM^^}                                         
       eval DBHOST=\$DBHOST_${SNM^^}                                           
       eval DBUSER=\$DBUSER_${SNM^^}
       eval DBPASS=\$DBPASS_${SNM^^}
       eval PNM=\$PNM_${SNM^^}
       eval CRYPTO_BACK=\$CRYPTO_BACK_${SNM^^}
       eval KYC=\$KYC_${SNM^^}
       eval HTTPS_MODE=\$HTTPS_MODE_${SNM^^}
       eval ACCESS_TOKEN=\$ACCESS_TOKEN_${SNM^^}
       eval API=\$API_${SNM^^}
       eval COMP=\$COMP_${SNM^^}
       eval NET=\$NET_${SNM^^}
       eval CONS=\$CONS_${SNM^^} 
                                             
 
        #export COMPOSE_PROJECT_NAME=1 G=$GENESIS C=c1 N=1 API=8108 COMP=4104 NET=8101 CONS=5051;docker-compose -f docker/$FCOMPOSE $mode
        export COMPOSE_PROJECT_NAME=$SNM G=$GENESIS C=$CLUST N=$NODE API=$API COMP=$COMP NET=$NET CONS=$CONS \
               GENESIS=$GENESIS SINGLE=$SINGLE PCONTROL=$PCONTROL PEERING=$PEERING NETWORK=$NETWORK \
               METRIC=$METRIC SIGNED=$SIGNED INFLUXDB=$INFLUXDB DBHOST=$DBHOST DBUSER=$DBUSER DBPASS=$DBPASS \
               PNM=$PNM CRYPTO_BACK=$CRYPTO_BACK KYC=$KYC HTTPS_MODE=$HTTPS_MODE; \
               $COMPOSE -f $FCOMPOSE $CMD $@;                           
       
   else                                                                              
       echo -e $CRED "Create and add $FCOMPOSE"   $CDEF                      
   fi                                                                                

}

                                                                                                       

function doServiceCmd {
  
  if [ $SNM == 'all' ];then

    for SNM in $PEER_LIST  
    do
        #echo "... $SNM"
        doDgtCompose $@
    done
  else
  # single DGT service control
    
    doDgtCompose $@
  fi


}
function doImageLoad {
# load docker image 
    if test -f plc-$DISTR.tgz; then 
        echo "Import docker image plc-$DISTR.tgz"
        docker load -i  plc-$DISTR.tgz && docker images | grep plc-$DISTR
    else
        echo "Can't find image plc-$DISTR.tgz"
    fi
}

function doImageSave {
# save docker image 
    if test -f plc-$DISTR.tgz; then 
        echo "Image plc-$DISTR already saved"
        
        
    else
        echo "Save docker image plc-$DISTR"
        docker save -o plc-$DISTR.tgz  plc-$DISTR 
    fi
}
function doListDgt {

    if [[ $1 == '-v' ]]; then           
                                        
      for NM in ${PEER_LIST[@]}              
      do                                
          doShowDgt $NM               
      done                              
    else                                
    # 
      echo -e $CBLUE "DGT PEER LIST:: ${PEER_LIST[@]}"  $CDEF                
    fi                                  



}
function doShowDgt { 
  NM=${1:-$SNM}

        eval PEER=\$PEER_${NM^^}
                          
        if [ -z ${PEER} ] ;then  
            echo -e $CRED "NO SUCH $NM DGT PEER " $CDEF
            return 
        fi
        echo -e $CBLUE "DGT PEER  $NM::" $CDEF
        for var in ${PEER_PARAMS[@]}
        do
            p_val="${var}_${NM^^}"
            
            echo -e $CBLUE "  $var=${!p_val} " $CDEF

        done
   
                         
} 
function doCopyDgt { 
        eval PEER=\$PEER_${SNM^^}
                          
        if [ -z ${PEER} ] || [ -z ${1} ] ;then  
            echo -e $CRED "NO SUCH $SNM DGT PEER OR UNDEF TARGET PEER" $CDEF
            return 
        fi
        if [[ ${SNM} == ${1} ]] ;then
          echo -e $CRED "SET NEW PEER NAME NOT EQUAL $SNM" $CDEF
          return

        fi 
        echo -e $CBLUE "COPY ${SNM^^} DGT PEER INTO ${1^^}" $CDEF

        PEER_LIST+=($1)
        updatePeerList "$LNAME" "${PEER_LIST[@]}"

        echo "" >> $FILE_ENV                             
        echo "######### >> ${1^^} PEER ##########" >> $FILE_ENV  
        
        for var in ${PEER_PARAMS[@]}
        do
            p_val="${var}_${SNM^^}"
            
            if [[ ${!p_val} == *"$delim"* ]]; then                       
                echo "${var}_${1^^}=\"${!p_val}\""   >> $FILE_ENV    
            else                                                     
                echo "${var}_${1^^}=${!p_val}"   >> $FILE_ENV        
            fi                                                       


        done
        echo "######### << ${1^^} DGT PEER ##########" >> $FILE_ENV
                         
}                        
function updateEnvParam {

 if [[ $2 != $3 ]]; then       
 echo -e  $CBLUE "update:: $1=$2 -> $3" $CDEF
 sed -i "s/$1=.*/$1=$3/"  $FILE_ENV
 fi                                   

}
function updatePeerList {
nlist=$1;shift
lval="($@)"
 #echo "s/${nlist}=.*/${nlist}=${lval}/"
 sed -i "s/${nlist}=.*/${nlist}=${lval}/"  $FILE_ENV


}
getParamHelp() {
  local name=$1
  local phelp=
    if [ -v PARAMS_HELP[$name] ]; then
       phelp="(${PARAMS_HELP[$name]})"
    fi

  echo $phelp



}
function doEditDgt {  
eval PEER=\$PEER_${SNM^^}
    
    if [ -z ${PEER} ];then           
      echo -e $CRED "DGT PEER '${SNM^^}' UNDEFINED" $CDEF
      return
    fi 
    

    #echo -e $CBLUE "EDIT ${SNM^^} DGT PEER " $CDEF
    if [[ $1 != "" ]]; then 
         PAR="$1_${SNM^^}"
         if [[ -v ${PAR} ]]; then
          #echo "UPDATE only $PAR = ${!PAR} "
          #echo -e $CBLUE "EDIT ${SNM^^} DGT PEER only param $1" $CDEF
          
          pvals=$(getParamHelp $1)
          echo -e $CBLUE "Set new value $pvals for ${SNM^^} DGT PEER" $CDEF
          read -e -p ">>> " -i "${!PAR}" NVAL   #-p "Set new value $pvals >>"
          if [[ $NVAL == *"$delim"* ]]; then
          updateEnvParam $PAR "${!PAR}" "\"$NVAL\""
          else
          updateEnvParam $PAR "${!PAR}" "$NVAL"
          fi
     
         else
           echo -e $CRED "UNDEFINED PARAM '$1' USE (${PEER_PARAMS[@]})" $CDEF
           
         fi
         return
    fi
    


    echo -e $CBLUE "EDIT ${SNM^^} DGT PEER " $CDEF
    for var in ${PEER_PARAMS[@]}
    do
       p_val="${var}_${SNM^^}"
       pvals=$(getParamHelp $var)
       echo -e $CBLUE "Update $var value $pvals" $CDEF
       read -e -p ">>> " -i "${!p_val}" NVAL  # "Set new value $var::"
       
       if [[ $NVAL == *"$delim"* ]]; then
             updateEnvParam $p_val "${!p_val}" "\"$NVAL\""
       else
             updateEnvParam $p_val "${!p_val}" "$NVAL"
       fi
    done
                                                                                                                
}                                                                                                               

function doAddDgt {

eval PEER=\$PEER_${SNM^^}
    
    if [ ! -z ${PEER} ];then           
      echo -e $CRED "DGT PEER '$PEER' ALREADY DEFINED" $CDEF
      return
    fi 

    PEER_LIST+=($SNM)               
    updatePeerList $LNAME "${PEER_LIST[@]}"     

    
    echo "ADD ${SNM^^} DGT PEER"
    
    echo "" >> $FILE_ENV
    echo "######### >> ${SNM^^} PEER ##########" >> $FILE_ENV
    for var in ${PEER_PARAMS[@]}
    do
    p_val="${var}_${NPROTO^^}"
    
    
    read -e -p "Set value for $var::" -i "${!p_val}" NVAL
    echo -e $CBLUE "  $var=$NVAL " $CDEF
    if [[ $NVAL == *"$delim"* ]]; then
        echo "${var}_${SNM^^}=\"${NVAL}\""   >> $FILE_ENV
    else
        echo "${var}_${SNM^^}=${NVAL}"   >> $FILE_ENV
    fi
    done
    echo "######### << ${SNM^^} DGT PEER ##########" >> $FILE_ENV


}

function doDelDgt {
  # sed '/the/d' dummy.txt
  eval PEER=\$PEER_${SNM^^}
  if [ -z ${PEER} ];then           
    echo -e $CRED "'$SNM' DGT PEER UNDEFINED" $CDEF
    return
  fi 
  read -e -p "Drop DGT PEER ${SNM^^} declaration (Y/N)?" -i "N" REPL
  if [[ $REPL == "Y" ]]; then
   echo -e $CBLUE "DROP ${SNM^^} DGT PEER "  $CDEF

   PEER_LIST=(${PEER_LIST[@]/$SNM})
   updatePeerList $LNAME "${PEER_LIST[@]}"

   cmd="/>> ${SNM^^}/,/<< ${SNM^^}/d"
   
   sed -i -e "$cmd" $FILE_ENV
   # for old version
   for var in ${PEER_PARAMS[@]}   
   do 
        cmd="/${var}_${SNM^^}=/d"
        sed -i -e "$cmd" $FILE_ENV
   done                               

  fi


}

function doShellDgt {
    
    eval CLUST=\$CLUST_${SNM^^}
    eval NODE=\$NODE_${SNM^^}
    if [ -z ${CLUST} ] || [ -z ${NODE} ];then   
      echo -e $CRED "UDEFINED PEER '$SNM' " $CDEF        
      return
    fi

    docker exec -it shell-dgt-${CLUST}-${NODE} bash

}

CMD=$1
shift
case $CMD in
     up)
          doDgtCompose  $@
          ;;
     down)
          doDgtCompose  $@
          ;;
     start)                  
         doDgtCompose  $@  
         ;;                
     stop)
          doDgtCompose  $@
          ;;
     restart)                      
          doDgtCompose  $@      
          ;;      
     build)                       
          doDgtCompose  $@              
          ;;   
     load)
          doImageLoad  $@              
          ;;              
     save)                    
          doImageSave  $@      
          ;;  
     list)                           
          doListDgt $@                   
          ;;           
     show)                  
          doShowDgt  $@                  
          ;;    
     edit)                        
          doEditDgt  $@                        
          ;;            
     add)                    
          doAddDgt  $@                    
          ;; 
     copy)                     
          doCopyDgt  $@                 
          ;;                           
     del)                             
          doDelDgt  $@                 
          ;;
     shell)
         doShellDgt $@
         ;;    
                    
     *)

          echo "Undefined cmd '$CMD' use <peer name> (up/up -d/down/start/stop/restart/list/show/edit/add/copy)"
          ;;
esac


