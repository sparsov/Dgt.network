# Copyright 2019 NTRLab
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ------------------------------------------------------------------------------
import logging
import copy
import time
import random
import os
import binascii
import json

from enum import Enum

LOGGER = logging.getLogger(__name__)
TOPOLOGY_SET_NM = 'bgx.consensus.pbft.nodes'
BGX_NESTS_NAME  = 'bgx.dag.nests'
TOPOLOGY_GENESIS_HEX = b'Genesis'.hex()

class PeerSync():
    inactive = 'inactive'
    active   = 'active'
    nosync   = 'nosync'

class PeerRole():
    leader = 'leader'
    plink  = 'plink'

class PeerAtr():
    endpoint   = 'endpoint'
    component  = 'component'
    node_state = 'node_state'
    cluster    = 'cluster'
    children   = 'children'
    name       = 'name'
    role       = 'role'
    delegate   = 'delegate'
    genesis    = 'genesis'
    ptype      = 'type'
    pid        = 'pid' 
    public     = 'public'  
    KYC        = 'KYC'
    maxpeer    = 'maxpeer'


class FbftTopology(object):
    """
    F-BFT topology 
    """
    def __init__(self):
        self._validator_id = None
        self._own_role = PeerRole.plink
        self._is_arbiter = False
        self._nest_colour = None # own cluster name
        self._genesis_node = None # genesis key
        self._genesis = 'UNDEF'  # genesis cluster
        self._parent = None
        self._leader = None
        self._endpoint = None
        self._arbiters = {}    # my arbiters 
        self._leaders  = {}    # leadres of other clusters
        self._publics  = []    # public clusters
        self._cluster = None   # own cluster
        self._topology  = {PeerAtr.children:{}}
        self._nosync = False

    @property
    def nest_colour(self):
        return self._nest_colour

    @property
    def own_role(self):
        return self._own_role
    @property
    def is_arbiter(self):
        return self._is_arbiter

    @property
    def is_leader(self):
        return self.own_role == PeerRole.leader

    @property
    def cluster(self):
        return self._cluster if self._cluster else {}

    @property
    def arbiters(self):
        return self._arbiters

    @property
    def leaders(self):
        return self._leaders

    @property
    def genesis(self):
        return self._genesis

    @property
    def genesis_node(self):
        return self._genesis_node if self._genesis_node else ''

    @property
    def topology(self):
        return self._topology

    def cluster_peer_role_by_key(self,key):
        return self._cluster[key][PeerAtr.role] if key in self._cluster else 'UNDEF'

    def get_topology_iter_from(self,root):
        return self.get_topology_iter(root)
     
    def get_topology_iter(self, root=None):
        def iter_topology(children):
            for key,peer in children.items():
                #print("iter_topology key ",key)
                yield key,peer
                if isinstance(peer,dict) and PeerAtr.cluster in peer :
                    cluster = peer[PeerAtr.cluster]
                    if PeerAtr.name in cluster and PeerAtr.children in cluster:
                        #LOGGER.debug("iter_topology >>> %s",cluster['name'])
                        yield from iter_topology(cluster[PeerAtr.children])
                        #LOGGER.debug("iter_topology <<< %s",cluster['name'])
                        
        #check children FIXME    
        return iter_topology(self._topology[PeerAtr.children] if root is None else root)


    def get_topology_iter1(self, root=None):
        # search peer and its cluster
        def iter_topology(children,parent):
            for key,peer in children.items():
                #print("iter_topology key ",key)
                yield key,(peer,parent)
                if isinstance(peer,dict) and PeerAtr.cluster in peer :
                    cluster = peer[PeerAtr.cluster]
                    if PeerAtr.name in cluster and PeerAtr.children in cluster:
                        #LOGGER.debug("iter_topology >>> %s",cluster['name'])
                        yield from iter_topology(cluster[PeerAtr.children],cluster)
                        #LOGGER.debug("iter_topology <<< %s",cluster['name'])

        #check children FIXME    
        return iter_topology(self._topology[PeerAtr.children],self._topology) # if root is None else root)

    def __iter__(self):
        return self.get_topology_iter()

    def get_cluster_iter(self, cname,cluster=None):
        def iter_cluster(children):
            for key,peer in children.items():
                print("iter_cluster key ",key)
                yield key,peer
        if cluster is None:
            cluster = self.get_cluster_by_name(cname)
        return iter_cluster(cluster[PeerAtr.children]) if cluster else []

    def get_cluster_leader(self,cluster):
        for key,peer in cluster[PeerAtr.children].items():
            if peer[PeerAtr.role] == PeerRole.leader :
                return peer
        return None

    def change_cluster_leader(self,cname,npeer):
        """
        for Validator
        """
        n = 0
        nkey = None
        cluster = self.get_cluster_by_name(cname)
        for key,peer in self.get_cluster_iter(cname,cluster): 
            if n == 2:
                return True,nkey
            if peer[PeerAtr.name] == npeer:                                     
                LOGGER.debug('TOPOLOGY set NEW LEADER %s.%s=%s',cname,npeer,peer)      
                peer[PeerAtr.role] = PeerRole.leader
                if key == self._validator_id:
                    # I am new leader - I should communicate with arbiters 
                    self._own_role = PeerRole.leader
                    LOGGER.debug('I AM NEW LEADER arbiters=%s',len(self._arbiters))
                else:
                    # new leader into other cluster
                    self._leaders[key] = (PeerRole.leader,cname,cluster[PeerAtr.children])
                nkey = key
                n += 1
                """
                if self.own_role == PeerRole.leader:
                    # others cluster leader was changed - update arbiters
                    self._arbiters[key] = (PeerAtr.delegate,cname,cluster[PeerAtr.children])
                    LOGGER.debug('TOPOLOGY ADD ARBITER for=%s',cname)
                    # new leader already connected - inform consensus
                """
            elif peer[PeerAtr.role] == PeerRole.leader :                                 
                LOGGER.debug('TOPOLOGY old LEADER=%s to plink',peer)                              
                peer[PeerAtr.role] = PeerRole.plink
                if key in self._leaders:
                    del self._leaders[key] 
                n += 1 
        return False,nkey
                                                     
    def change_current_leader(self,npid,cname):
        """
        for Engine - new leader key(npid) into cluster(cname)  
        """
        i_am_new_leader = False
        if npid not in self._cluster:
            # other cluster
            cluster = self.get_cluster_by_name(cname)
            if cluster is None or PeerAtr.children not in cluster:
                return False,i_am_new_leader
            cluster = cluster[PeerAtr.children]
        else:
            cluster = self._cluster

        for key,peer in cluster.items():
            if peer[PeerAtr.role] == PeerRole.leader :
                LOGGER.debug('TOPOLOGY old LEADER=%s to plink',peer)                              
                peer[PeerAtr.role] = PeerRole.plink
                if key == self._validator_id:
                    self._own_role = PeerRole.plink
                break
        peer = cluster[npid]
        peer[PeerAtr.role] = PeerRole.leader
        if npid == self._validator_id:
            self._own_role = PeerRole.leader
            i_am_new_leader = True
            LOGGER.debug('I AM NEW LEADER arbiters=%s',len(self._arbiters))
        """
        if self.own_role == PeerRole.leader and npid not in self._arbiters:
            # I am leader
            self._arbiters[npid] = (PeerAtr.delegate,cname,cluster)
            LOGGER.debug('TOPOLOGY ADD ARBITER for=%s',cname)
        """
        LOGGER.debug('TOPOLOGY set NEW LEADER %s',peer)
        return True,i_am_new_leader

    def _switch_off_arbiter(self,peer,key):
        LOGGER.debug('TOPOLOGY old ARBITER=%s',peer)     
        peer[PeerAtr.delegate] = False
        try:
            del self._arbiters[key]
        except KeyError:
            pass
        if key == self._validator_id:                    
            self._is_arbiter = False  

    def _switch_on_arbiter(self,cname,cluster,peer,key):
                                            
        peer[PeerAtr.delegate] = True                                                                         
        if key == self._validator_id:                                                                         
            # I am new arbiter - I should communicate with arbiters and leaders                               
            self._is_arbiter = True                                                                                     
            LOGGER.debug('I AM NEW ARBITER=%s',len(self._arbiters))                                           
        elif self.own_role == PeerRole.leader or (PeerAtr.delegate in peer and peer[PeerAtr.delegate]):  
            if key not in self._arbiters:
                self._arbiters[key] = (PeerAtr.delegate,cname,cluster)                          
            LOGGER.debug('TOPOLOGY ADD ARBITER for=%s total=%s',cname,len(self._arbiters))                                                 
                               
    def change_cluster_arbiter(self,cname,npeer):
        """
        New arbiter into cluster
        """
        n = 0
        nkey = None
        cluster = self.get_cluster_by_name(cname)
        for key,peer in self.get_cluster_iter(cname,cluster): 
            if n == 2:
                return True,nkey
            if peer[PeerAtr.name] == npeer:                                     
                LOGGER.debug('TOPOLOGY set NEW ARBITER %s.%s=%s',cname,npeer,peer)  
                self._switch_on_arbiter(cname,cluster[PeerAtr.children],peer,key)    
                nkey = key
                n += 1
                
            elif PeerAtr.delegate in peer and peer[PeerAtr.delegate] :
                """
                drop old arbiter from arbiter list
                """     
                self._switch_off_arbiter(peer,key)                            
                n += 1 
        return False,nkey

    def change_current_arbiter(self,npid,cname):                                       
        """                                                                           
        new arbiter key(npid) into cluster(cname)                                      
        """                                                                           
        if npid not in self._cluster:                                                 
            # other cluster                                                           
            cluster = self.get_cluster_by_name(cname)                                 
            if cluster is None or PeerAtr.children not in cluster:                    
                return False,False                                          
            cluster = cluster[PeerAtr.children]                                       
        else:                                                                         
            cluster = self._cluster                                                   
                                                                                      
        for key,peer in cluster.items():                                              
            if PeerAtr.delegate in peer and peer[PeerAtr.delegate]: 
                self._switch_off_arbiter(peer,key)
                break
        # set new arbiter                                                                      
        peer = cluster[npid]
        self._switch_on_arbiter(cname,cluster,peer,npid) 
        return True,(npid == self._validator_id)                                                   

    def del_peers(self,cname,pold):
        """
        Del peers from cluster cname
        """
        cluster = self.get_cluster_by_name(cname)
        if cluster is None:
            return False,"Undefined cluster {}".format(cname)

        try:
            peers = json.loads(pold.replace("'",'"'))
        except ValueError as e:
            return False,'Invalid json: '+ str(e)
        n = 0
        children = cluster[PeerAtr.children]
        for key,opeer in peers.items():
            if key in children:
                LOGGER.debug('DEL PEER=%s INTO %s',key[:8],cname)
                del children[key]
                n = n + 1
        if n == 0 :
            return False,"There are no peers for del into cluster {}".format(cname)
        return True,None

    def add_new_peers(self,cname,pnew):
        """
        Add new peer into cluster cname
        """
        cluster = self.get_cluster_by_name(cname)
        try:
            peers = json.loads(pnew.replace("'",'"'))
        except ValueError as e:
            return False,'Invalid json: '+ str(e)

        if cluster is None:
            return False,"Undefined cluster {}".format(cname)
        children = cluster[PeerAtr.children]
        #LOGGER.debug('ADD NEW PEER=%s INTO %s',peers,cname)
        for key,npeer in peers.items():
            peer = self.peer_is_exist(key)
            if peer is None:
                if (PeerAtr.delegate in npeer and npeer[PeerAtr.delegate]) or (PeerAtr.role in npeer and npeer[PeerAtr.role] == PeerRole.leader and len(children) > 0):
                    return False,"New peer with key={} can't be leader or arbiter".format(key[:8])
                else:
                    LOGGER.debug('ADD NEW PEER=%s : %s INTO %s',key[:8],npeer,cname)
                    children[key] = npeer
            else:
                return False,"Peer {} with key={} already exist".format(peer,key[:8])

        return True,None

    def add_new_cluster(self,cname,pname,clist,ppeer=None):
        """
        add new cluster
        """
        if ppeer is None:
            ppeer,_ = self.get_peer_by_name(cname,pname)
        if ppeer is None:
            return False,"Peer {}.{} does not exist".format(cname,pname)
        if PeerAtr.cluster in ppeer:
            return False,"Peer {}.{} already cluster owner".format(cname,pname)

        try: # {'name': 'Bgx2', 'type': 'cluster'}
            ncluster = json.loads(clist.replace("'",'"'))
        except ValueError as e:
            return False,'Invalid json: '+ str(e)

        if PeerAtr.name in ncluster and PeerAtr.ptype in ncluster :
            cluster = self.get_cluster_by_name(ncluster[PeerAtr.name])
            if cluster is not None:
                return False,"Cluster {} already exist".format(cname)
            ncluster[PeerAtr.children] = {}
            ppeer[PeerAtr.cluster] = ncluster
        else:
            return False,"Undefined new cluster params"

        return True,None

    def del_cluster(self,cname,pname,ppeer=None):
        # del empty cluster
        if ppeer is None:
            ppeer,_ = self.get_peer_by_name(cname,pname)
        if ppeer is None:
            return False,"Peer {}.{} does not exist".format(cname,pname)
        if PeerAtr.cluster not in ppeer:
            return False,"Peer {}.{} is not cluster owner".format(cname,pname)
        cluster = ppeer[PeerAtr.cluster]
        if len(cluster[PeerAtr.children]) > 0:
            return False,"Cluster {} for {}.{} is not empty".format(cluster[PeerAtr.name],cname,pname)
        del ppeer[PeerAtr.cluster]
        return True,None

    def peer_is_exist(self,peer_key):
        for key,peer in self.get_topology_iter():
            if (key == peer_key):
                return peer
        return None

    def key_to_peer(self,peer_key):
        # get peer and it cluster by key 
        for key,peer in self.get_topology_iter1():
            if (key == peer_key):
                return peer
        return None,None
    def get_position_in_public(self):
        
        for cluster in self._publics:
            pmax = (cluster[PeerAtr.maxpeer] if PeerAtr.maxpeer in cluster else 7)
            LOGGER.debug('check : cluster=%s peers=%s~%s',cluster[PeerAtr.name],len(cluster[PeerAtr.children]),pmax)
            if len(cluster[PeerAtr.children]) < (cluster[PeerAtr.maxpeer] if PeerAtr.maxpeer in cluster else 7):
                return cluster[PeerAtr.name],cluster
        return None,None
    def peer_to_cluster_name(self,peer_key):
        if peer_key == TOPOLOGY_GENESIS_HEX:
            return 'Genesis'
        peer = self.peer_is_exist(peer_key)
        if peer and (PeerAtr.cluster in peer) :
            cluster = peer[PeerAtr.cluster]
            return cluster[PeerAtr.name]
        return None



    def peer_is_leader(self,peer_key):
        peer = self.peer_is_exist(peer_key)
        if peer and (PeerAtr.role in peer) and peer[PeerAtr.role] == PeerRole.leader :
            return True
        LOGGER.debug('peer_is_leader: is not leader=%s',peer_key[:8])
        return False
    
    def update_peer_activity(self,peer_key,endpoint,mode,sync=False,force=False,pid=None):
        
        for key,peer in self.get_topology_iter():
            if (peer_key is not None and key == peer_key) or (PeerAtr.endpoint in peer and peer[PeerAtr.endpoint] == endpoint)  :
                if endpoint is not None:
                    peer[PeerAtr.endpoint] = endpoint
                if pid is not None:
                    peer[PeerAtr.pid] = pid
                #if sync or (not sync and (peer[PeerAtr.node_state] != PeerSync.active or force)) :
                peer[PeerAtr.node_state] = (PeerSync.active if sync else PeerSync.nosync) if mode else PeerSync.inactive
                """
                if component is not None:
                    peer[PeerAtr.component] = component
                    LOGGER.debug("UPDATE peer_component=%s  peer=%s",component,peer)
                """
                if not sync and not self._nosync:
                    self._nosync = True
                    self._topology['sync'] = not self._nosync 
                LOGGER.debug("UPDATE peer_activity: nosync=%s peer=%s endpoint=%s",self._nosync,peer,endpoint)
                return key
        return None

    def get_peer(self,peer_key):
        if self._cluster is None:
            return None
        if peer_key in self._cluster:
            peer = self._cluster[peer_key]
            return peer
        else:
            for key,peer in self.get_topology_iter():
                if key == peer_key:
                    return peer
        return  None

    def get_peer_state(self,peer_key,peer=None):
        if peer is None:
            peer = self.get_peer(peer_key)
        if peer is not None and PeerAtr.node_state in peer:
            return peer[PeerAtr.node_state]
        return  PeerSync.inactive

    def get_peer_id(self,peer_key):
        peer = self.get_peer(peer_key)
        if peer is not None and PeerAtr.pid in peer:
            return peer[PeerAtr.pid]
        return  None

    def get_cluster_by_name(self,cname):
        if cname == 'Genesis':
            return self._topology #[PeerAtr.children]

        for key,peer in self.get_topology_iter(): #self._topology): # [PeerAtr.children]
            if isinstance(peer,dict) and PeerAtr.cluster in peer :
                #print('PEE',key,type(peer),peer,type(self._topology))
                cluster = peer[PeerAtr.cluster]
                #print('CLA ',cluster[PeerAtr.name])
                if PeerAtr.name in cluster and PeerAtr.children in cluster and cluster[PeerAtr.name] == cname:
                    return cluster
        return None

    def get_cluster_owner(self,cname):
        if cname == 'Genesis':
            return TOPOLOGY_GENESIS_HEX

        for key,peer in self.get_topology_iter(): #self._topology): # [PeerAtr.children]
            if isinstance(peer,dict) and PeerAtr.cluster in peer :
                #print('PEE',key,type(peer),peer,type(self._topology))
                cluster = peer[PeerAtr.cluster]
                #print('CLA ',cluster[PeerAtr.name])
                if PeerAtr.name in cluster and PeerAtr.children in cluster and cluster[PeerAtr.name] == cname:
                    return key
        return None


    def get_cluster_arbiter(self,cname):
        cluster = self.get_cluster_by_name(cname)

    
    def get_peer_by_name(self,cname,name):
        cluster = self.get_cluster_by_name(cname)
        if cluster is None:
            return None,None
        for key,peer in cluster[PeerAtr.children].items():
            if PeerAtr.name in peer and peer[PeerAtr.name] == name:
                return peer,key
        """
        for key,peer in self.get_topology_iter():
            if PeerAtr.cluster in peer:
                cluster = peer[PeerAtr.cluster]
                if PeerAtr.name in cluster and PeerAtr.children in cluster and cluster[PeerAtr.name] == cname:
                    for skey,speer in cluster[PeerAtr.children].items():
                        #print('SPEER',speer,speer[PeerAtr.name] == cname)
                        if PeerAtr.name in speer and speer[PeerAtr.ptype] == 'peer' and speer[PeerAtr.name] == name:
                            return speer
        """
        return None,None

    def update_peer_component(self,peer_key,component=None):
        for key,peer in self.get_topology_iter():
            if (peer_key is not None and key == peer_key)  :
                if component is not None:
                    peer[PeerAtr.component] = component
                    LOGGER.debug("UPDATE peer_component=%s  peer=%s",component,peer)
                break


    def get_topology(self,topology,validator_id,endpoint,peering_mode='static'):
        # get topology from string

        def get_cluster_info(arbiter_id,parent_name,name,children):
            for key,peer in children.items():
                #LOGGER.debug('[%s]:child=%s val=%s',name,key[:8],val)
                if key == self._validator_id:
                    if arbiter_id is not None:
                        self._arbiters[arbiter_id] = ('arbiter',parent_name)
                    self._nest_colour = name
                    self._cluster    = children
                    self._parent     = arbiter_id
                    if PeerAtr.role in peer:
                        self._own_role = peer[PeerAtr.role]
                    if PeerAtr.delegate in peer:
                        self._is_arbiter = peer[PeerAtr.delegate]
                    #  yourself 
                    peer[PeerAtr.endpoint] = endpoint
                    peer[PeerAtr.node_state] = PeerSync.active
                    LOGGER.debug('Found own NEST=%s validator_id=%s',name,self._validator_id)
                    return

                if PeerAtr.cluster in peer:
                    cluster = peer[PeerAtr.cluster]
                    if PeerAtr.name in cluster and PeerAtr.children in cluster:
                        get_cluster_info(key,name,cluster[PeerAtr.name],cluster[PeerAtr.children])
                        if self._nest_colour is not None:
                            return

        def get_arbiters(arbiter_id,name,children):
            # make ring of arbiter - add only arbiter from other cluster
            for key,peer in children.items():
                if self._nest_colour != name:
                    # check only other cluster and add delegate
                    if PeerAtr.delegate in peer:
                        self._arbiters[key] = (PeerAtr.delegate,name,children)
                        #if arbiter_id == self._parent:
                        #    self._leader = key
                    if PeerAtr.role in peer and peer[PeerAtr.role] == PeerRole.leader:
                        # add into leaders list
                        self._leaders[key] = (PeerRole.leader,name,children)

                if self._genesis_node is None and PeerAtr.genesis in peer:
                    # this is genesis node of all network
                    self._genesis_node = key
                if PeerAtr.cluster in peer:
                    cluster = peer[PeerAtr.cluster]
                    if PeerAtr.name in cluster and PeerAtr.children in cluster:
                        if PeerAtr.public in cluster and cluster[PeerAtr.public]:
                            # add public cluster into list
                            self._publics.append(cluster)
                        get_arbiters(key,cluster[PeerAtr.name],cluster[PeerAtr.children])

        #topology = json.loads(stopology)
        self._validator_id = validator_id
        self._endpoint = endpoint
        self._topology = topology if topology != {} else {PeerAtr.children:{}}
        #LOGGER.debug('get_topology=%s',topology)
        topology['topology'] = peering_mode
        topology['sync'] = not self._nosync
        if PeerAtr.name in topology and PeerAtr.children in topology:
            self._genesis  = topology['name'] # genesis cluster
            get_cluster_info(None,None,topology[PeerAtr.name],topology[PeerAtr.children])
        if self._nest_colour is None:
            pass
            #self._nest_colour = 'Genesis'
        else:
            # get arbiters
            get_arbiters(None,topology[PeerAtr.name],topology[PeerAtr.children])
            for key,peer in self._cluster.items():
                if peer[PeerAtr.role] == PeerRole.leader:
                    self._leader = key
                    break
            # add Identity
            topology['Network'] = 'DGT TEST network'
            topology['Identity'] = {'PubKey': self._validator_id,
                                    'IP' : self._endpoint,
                                    'Cluster' : self._nest_colour,
                                    'Genesis' : self._genesis_node,
                                    'Leader'  : self._leader if self._leader else 'UNDEF',
                                    'Parent'  : self._parent if self._parent else 'UNDEF',
                                    'KYCKey'  : '0ABD7E'

            }
            LOGGER.debug('Arbiters RING=%s GENESIS=%s PUBLICS=%s', self._arbiters, self.genesis_node[:8], len(self._publics))





