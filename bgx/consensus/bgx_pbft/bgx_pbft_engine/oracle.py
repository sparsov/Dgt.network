# Copyright 2018 NTRlab
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
# -----------------------------------------------------------------------------

import logging
import os
import binascii
import time
import json

import sawtooth_signing as signing
from sawtooth_signing import CryptoFactory
from sawtooth_signing.secp256k1 import Secp256k1PrivateKey

from sawtooth_sdk.consensus.exceptions import UnknownBlock,InvalidState
from sawtooth_sdk.messaging.stream import Stream
from sawtooth_sdk.protobuf.batch_pb2 import Batch
from sawtooth_sdk.protobuf.batch_pb2 import BatchHeader
from sawtooth_sdk.protobuf.client_batch_submit_pb2 import ClientBatchSubmitRequest
from sawtooth_sdk.protobuf.client_batch_submit_pb2 import ClientBatchSubmitResponse
from sawtooth_sdk.protobuf.client_block_pb2 import ClientBlockGetByTransactionIdRequest
from sawtooth_sdk.protobuf.client_block_pb2 import ClientBlockGetResponse
from sawtooth_sdk.protobuf.block_pb2 import BlockHeader
from sawtooth_sdk.protobuf.consensus_pb2 import ConsensusBlock, ConsensusNotifyPeerConnected
from sawtooth_sdk.protobuf.validator_pb2 import Message


from bgx_pbft.consensus.pbft_block_publisher import PbftBlockPublisher
from bgx_pbft.consensus.pbft_block_verifier  import PbftBlockVerifier
from bgx_pbft.consensus.pbft_fork_resolver import PbftForkResolver
from bgx_pbft.consensus.consensus_state import ConsensusState
from bgx_pbft.consensus.consensus_state_store import ConsensusStateStore
# for getting settings
from bgx_pbft.consensus.pbft_settings_view import PbftSettingsView
from bgx_pbft.journal.block_wrapper import BlockWrapper


from bgx_pbft_common.protobuf.pbft_consensus_pb2 import PbftMessage,PbftMessageInfo,PbftBlockMessage,PbftViewChange
from bgx_pbft_common.utils import _short_id
# for nests making
from  sawtooth_settings.protobuf.settings_pb2 import SettingProposal
from  sawtooth_settings.protobuf.settings_pb2 import SettingsPayload
from bgx_pbft_common.utils import _config_inputs,_config_outputs
try:
    import sawtooth_sdk.protobuf.transaction_pb2 as txn_pb
except TypeError:
    import sawtooth_validator.protobuf.transaction_pb2 as txn_pb

from sawtooth_validator.gossip.fbft_topology import PeerSync,PeerRole,PeerAtr,FbftTopology,BGX_NESTS_NAME

import hashlib
import random

LOGGER = logging.getLogger(__name__)

_PLINK_   = 'plink'
_LEADER_  = 'leader'
_AUX_     = 'aux'
_ARBITER_ = 'arbiter'

_THE_SAME_ID_ = True # mode when we make chain with the same block ID 

class PbftOracle:
    """
    This is a wrapper around the PBFT structures (publisher,verifier, fork resolver) and their attendant proxies.
    """
    CONSENSUS_MSG = ['PrePrepare','Prepare','Commit','CheckPoint']

    def __init__(self, service, component_endpoint,config_dir, data_dir, key_dir):
        
        self._config_dir = config_dir
        self._data_dir = data_dir
        self._service = service
        LOGGER.debug('Stream key_dir=%s',key_dir)
        self._signer = _load_identity_signer(key_dir, 'validator')
        #self._setting_signer = _load_identity_signer('/root/.sawtooth/keys', 'my_key')
        self._validator_id = self._signer.get_public_key().as_hex()

        LOGGER.debug('Stream component_endpoint=%s ',component_endpoint)
        stream = Stream(component_endpoint)

        self._block_cache = _BlockCacheProxy(service, stream)
        self._state_view_factory = _StateViewFactoryProxy(service)

        self._batch_publisher = _BatchPublisherProxy(stream, self._signer) # self._signer)
        self._publisher = None
        self._consensus_state_store = ConsensusStateStore(data_dir=self._data_dir,validator_id=self._validator_id)
        state_view = BlockWrapper.state_view_for_block(
                block_wrapper=self._block_cache.block_store.chain_head,
                state_view_factory=self._state_view_factory)

        self._pbft_settings_view = PbftSettingsView(state_view)
        nodes = self._pbft_settings_view.pbft_nodes.replace("'",'"')
        self._authorized_keys = self._pbft_settings_view.authorized_keys
        LOGGER.debug("authorized_keys=%s\n",self._authorized_keys)
        #LOGGER.debug("pbft_settings_view DAG_STEP=%s NODES=%s",self.dag_step,nodes)
        self._fbft = FbftTopology()
        #self._nodes = json.loads(nodes)
        self._fbft.get_topology(json.loads(nodes),self._validator_id,'','static')
        LOGGER.debug('nodes=%s',nodes)
        """
        because we have some clusters we should search itself into nodes tree
        and for node of cluster we should know : parent and name of cluster,list of nodes which belonge our cluster,this node type
        """
        """
        self._node = None
        self._genesis_node = None
        self._cluster_name = None
        self._cluster = {}
        self._arbiters = {} # ring of arbiters
        if 'name' in self._nodes:
            self._genesis  = self._nodes['name'] # genesis cluster
            self.get_cluster_info(None,None,self._nodes['name'],self._nodes['children'])
            self.get_arbiters(None,self._nodes['name'],self._nodes['children'])
        else:
            self._genesis = 'UNDEF'      
            self._genesis_node = 'UNDEF' 
        #self._node = self._nodes[self._validator_id] if self._validator_id in self._nodes else 'plink'
        #LOGGER.debug('_validator_id=%s is [%s] cluster=%s',self._validator_id,self._node['role'],self._node['cluster'])
        """
        self._canceled = False
        #sid = self.get_validator_id().encode()
        #sidd = sid.decode()
        #LOGGER.debug('PbftOracle:: _validator_id %s %s..%s',sid,sidd[:8],sidd[-8:])

    @property
    def dag_step(self):
        return self._pbft_settings_view.dag_step
    @property
    def max_branch(self):
        return self._pbft_settings_view.max_branch

    @property
    def is_pbft_full(self):
        return self._pbft_settings_view.is_pbft_full

    @property
    def send_batches(self):
        return self._pbft_settings_view.send_batches

    @property
    def block_timeout(self):
        return self._pbft_settings_view.block_timeout

    @property
    def cluster(self):
        #LOGGER.debug('CLUSTER: %s ~ %s\n', self._fbft.cluster, self._cluster)
        return self._fbft.cluster

    @property
    def genesis(self):
        return self._fbft.genesis

    @property
    def genesis_node(self):
        return self._fbft.genesis_node

    @property
    def own_type(self):
        return self._fbft.own_role #self._node if self._node is not None else 'UNDEF'

    @property
    def cluster_name(self):
        #LOGGER.debug('CLUSTER NAME: %s ~ %s\n', self._fbft.nest_colour, self._cluster_name)
        return self._fbft.nest_colour 

    @property
    def arbiters(self):
        arbs = {key : (vals[0],ConsensusNotifyPeerConnected.STATUS_UNSET,vals[1]) for key,vals in self._fbft.arbiters.items()}
        LOGGER.debug('ASK ARBITERS: %s\n', arbs)
        return arbs

    @property
    def validator_id(self):
        return self._validator_id

    @property
    def authorized_keys(self):
        return self._authorized_keys
    """
    def get_arbiters(self,arbiter_id,name,children):
        # make ring of arbiter - add only arbiter from other cluster
        LOGGER.debug('get arbiters: cluster=%s children=%s self=%s',name,len(children),self._cluster_name)
        for key,val in children.items():
            if self._cluster_name != name:
                # check only other cluster and add delegate
                if 'delegate' in val:
                    self._arbiters[key] = ('delegate',ConsensusNotifyPeerConnected.STATUS_UNSET,name)

            if self._genesis_node is None and 'genesis' in val:
                # this is genesis node of all network
                self._genesis_node = key

            if 'cluster' in val:
                cluster = val['cluster']
                if 'name' in cluster and 'children' in cluster:
                    self.get_arbiters(key,cluster['name'],cluster['children'])
                    
    
    def get_cluster_info(self,arbiter_id,parent_name,name,children):
        LOGGER.debug('cluster_info=%s children=%s',name,len(children))
        for key,val in children.items():
            LOGGER.debug('[%s]:child=%s val=%s',name,key[:8],val)
            if self._node is None and key == self._validator_id:
                #
                #this is me - stop searching
                #set own node type and cluster info
                #
                self._node = val['role'] if 'role' in val else 'plink'
                #
                #if arbiter_id is not None:
                #    self._arbiters[arbiter_id] = ('arbiter',False,parent_name)  # type of arbiter and status(not ready)
                #
                self._cluster = children
                self._cluster_name = name 
                LOGGER.debug('Found own validator_id=%s is [%s] cluster=%s name=%s nodes=%s',self._validator_id,self._node,arbiter_id[:8] if arbiter_id else None,name,len(self._cluster))
                return
           
            if 'cluster' in val:
                cluster = val['cluster']
                if 'name' in cluster and 'children' in cluster:
                    self.get_cluster_info(key,name,cluster['name'],cluster['children'])
                    if self._node is not None:
                        return
                else:
                    LOGGER.debug('IGNORE bad cluster_info for node=%s:%s',name,key[:8])
    
    """

    
    def get_validator_id(self):
        return self._validator_id 

    def get_node_type_by_id(self,vid):
        #tp = self._cluster[vid]['role'] if vid in self._nodes else 'UNDEF' 
        #LOGGER.debug('GET_NODE_TYPE_BY_ID=%s ~ %s',tp,self._fbft.cluster_peer_role_by_key(vid))
        return self._fbft.cluster_peer_role_by_key(vid)

    def change_current_leader(self,npid,cluster):
        self._fbft.change_current_leader(npid,cluster)

    def make_nest_step(self,num,authorized_keys=None):
        """
        proposal request
        """
        #public_key_hash1 = hashlib.sha256(authorized_keys.encode() if authorized_keys is not None else self.authorized_keys.encode()).hexdigest()
        public_key_hash = authorized_keys if authorized_keys else self._validator_id #self.authorized_keys #self._signer.get_public_key().as_hex() # hashlib.sha256(block_header.signer_public_key.encode()).hexdigest()
        setting = BGX_NESTS_NAME
        nonce=hex(random.randint(0, 2**64))
        if True:
            # try to set pbft params

            proposal = SettingProposal(
                 setting=setting,
                 value=str(num),
                 nonce=nonce)
            payload = SettingsPayload(data=proposal.SerializeToString(),action=SettingsPayload.PROPOSE)
            serialized = payload.SerializeToString()
            input_addresses = _config_inputs(setting) 
            output_addresses = _config_outputs(setting)

            header = txn_pb.TransactionHeader(
                signer_public_key=public_key_hash, #self._signer.get_public_key().as_hex(),
                family_name='bgx_settings',
                family_version='1.0',
                inputs=input_addresses,
                outputs=output_addresses,
                dependencies=[],
                payload_sha512=hashlib.sha512(serialized).hexdigest(),
                batcher_public_key=public_key_hash, #self._signer.get_public_key().as_hex(),
                nonce=hex(random.randint(0, 2**64))).SerializeToString()

            signature = self._batch_publisher.identity_signer.sign(header)

            transaction = txn_pb.Transaction(
                    header=header,
                    payload=serialized,
                    header_signature=signature)

            #LOGGER.debug('payload action=%s nonce=%s public_key_hash=%s',payload.action,nonce,public_key_hash)

            self._batch_publisher.send([transaction])
        else:
            # get setting
            pass


    def initialize_block(self, previous_block):
        block_header = NewBlockHeader(
            previous_block,
            self._signer.get_public_key().as_hex()
            )

        self._publisher = PbftBlockPublisher(
            block_cache=self._block_cache,
            state_view_factory=self._state_view_factory,
            batch_publisher=self._batch_publisher,
            data_dir=self._data_dir,
            config_dir=self._config_dir,
            validator_id=self._validator_id,
            node = self.own_type
            )

        return self._publisher.initialize_block(block_header)

    def check_publish_block(self, block):
        #LOGGER.debug('PbftOracle:check_publish_block...')
        #self.start_consensus(self._publisher._block_header)
        return self._publisher.check_publish_block(self._publisher._block_header) #(block)

    def finalize_block(self, block):
        LOGGER.debug('PbftOracle:finalize_block...')
        return self._publisher.finalize_block(block)

    def verify_block(self, block):
        LOGGER.debug('PbftOracle:verify_block...')
        
        verifier = PbfBlockVerifier(
            block_cache=self._block_cache,
            state_view_factory=self._state_view_factory,
            data_dir=self._data_dir,
            config_dir=self._config_dir,
            validator_id=self._validator_id)

        return verifier.verify_block(block)

    def switch_forks(self, cur_fork_head, new_fork_head):
        '''"compare_forks" is not an intuitive name.'''
        LOGGER.debug('PbftOracle: switch_forks %s signer=%s~%s',cur_fork_head,cur_fork_head.signer_id.hex()[:8],new_fork_head.signer_id.hex()[:8])
        if new_fork_head.block_num == 0 and new_fork_head.block_num == cur_fork_head.block_num:
            # use genesis block from 
            is_genesis_node = new_fork_head.signer_id.hex() == self.genesis_node
            LOGGER.debug('PbftOracle: IS GENESIS_NODE=%s',is_genesis_node)
            return True if is_genesis_node else False

        if new_fork_head.block_num > cur_fork_head.block_num or (new_fork_head.block_num == cur_fork_head.block_num and new_fork_head.block_id > cur_fork_head.block_id) :
            
            """
            if new_fork_head.block_num == 0 and self.own_type == 'plink':
                LOGGER.debug('PbftOracle:switch_forks TRUE for LEADER')
                return False
            """
            LOGGER.debug('PbftOracle:switch_forks TRUE for new-num=%s cur-num=%s new-id=%s cur-id=%s',new_fork_head.block_num,cur_fork_head.block_num,_short_id(new_fork_head.block_id.hex()),_short_id(cur_fork_head.block_id.hex()))
            return True
        elif new_fork_head.block_num < cur_fork_head.block_num :
            #
            chain_block = cur_fork_head
            LOGGER.debug('PbftOracle: new_fork_head.block_num=%s < cur_fork_head.block_num=%s',new_fork_head.block_num,cur_fork_head.block_num)
            num = 0
            while(True): 
                chain_block = PbftBlock(self._service.get_blocks([chain_block.previous_id])[chain_block.previous_id]) 
                LOGGER.debug('PbftOracle: while chain_block.block_num=%s == new_fork_head.block_num=%s',chain_block.block_num,new_fork_head.block_num) 
                if chain_block.block_num == new_fork_head.block_num:
                    LOGGER.debug('PbftOracle: found block')
                    break
                num += 1 
            if new_fork_head.block_id > chain_block.block_id:
                LOGGER.debug('PbftOracle: switch to new forks')
                return True 
        else:
            # num is the same genesis for instance
            if new_fork_head.block_id != cur_fork_head.block_id:
                LOGGER.debug('PbftOracle: switch_forks HEAD MISMATCH')
                return False
            else:
                """
                This is our own block
                """
                if cur_fork_head.block_num == 0:
                    LOGGER.debug('PbftOracle: switch_forks TRUE blocks ID are the same') 
                    return True   
                else:
                    LOGGER.debug('PbftOracle: switch_forks FALSE blocks ID are the same')
                    return False

        LOGGER.debug('PbftOracle: switch_forks DONE FALSE')
        return False

    def get_consensus_state_for_block_id(self,block,force = True):
        block_id = block.block_id.hex()
        #LOGGER.debug("PbftOracle: get_consensus_state for block_id='%s' type(%s)",block_id,type(block))
        consensus_state = ConsensusState.consensus_state_for_block_id(
                block_id=block_id, #block_header.previous_block_id,
                block_cache=self._block_cache,
                state_view_factory=self._state_view_factory,
                consensus_state_store=self._consensus_state_store,
                node=self.own_type,
                force = force
                )
        return consensus_state

    def set_consensus_state_for_block_id(self,block_id,state):
        self._consensus_state_store[block_id] = state


    def start_consensus(self,block):
        """
        Have got NewBlock message
        """
        def is_new_block_valid():
            """
                Legitimacy is checked by:
                  1) looking at the signer_id of the block in the BlockNew message,
                  2) making sure the previous_id is valid as the current chain head.
                  3) the Consensus Seal is checked here as well
                  4) all nodes tentatively update their working blocks.
            """
            return True
        self._canceled = False
        #block_str = int2hex(block.block_num)
        block_id = block.block_id.hex()
        summary = block.summary.hex()
        signer_id  = block.signer_id.hex()
        block_num  = block.block_num
        LOGGER.info('=> NEW_BLOCK id=%s block_num=%s signer=%s.%s summary=%s prev_id=%s\n', _short_id(block_id),block_num,self.get_node_type_by_id(signer_id),_short_id(signer_id),_short_id(summary),_short_id(block.previous_id.hex()))
        LOGGER.debug("PbftOracle: start_consensus for block='%s'",_short_id(block_id))
        state = self.get_consensus_state_for_block_id(block) # create in case state is not exists 
        if state is not None:
            if state.is_step_NotStarted:
                LOGGER.debug('PbftOracle: START CONSENSUS for block_id=%s step=%s mode=%s',_short_id(block_id),state.step,state.mode)
                
                if not is_new_block_valid():
                    # ignore NewBlock
                    return False 

                state.next_step() # => PrePreparing
                state.set_summary(summary)
                state.set_new_block()
                self.set_consensus_state_for_block_id(block_id,state) # save new state
                
                """
                save info about block into cell indexed by summary
                """
                estate = self.get_state_by_summary(summary,"NEW_BLOCK")
                if estate is None:
                    state.set_block_id(block.block_id)
                    state.set_consensus_state_for_block_id(summary,self._consensus_state_store)
                else:
                    estate.set_block_id(block.block_id)
                    estate.set_consensus_state_for_block_id(summary,self._consensus_state_store)

                LOGGER.debug('PbftOracle: save block_id=%s for summary=%s',_short_id(block_id),_short_id(summary))
                if state.node == _LEADER_:
                    """
                     leader node - send prePrepare to plink nodes
                    """
                    if block_num == 0 or signer_id == self._validator_id:  # block_num == 0 or signer_id == self._validator_id
                        self._send_pre_prepare(state,block)
                        # we already have prePrepare message go to the new state
                        state.next_step() # => Preparing
                        self.set_consensus_state_for_block_id(block_id,state)
                        LOGGER.debug('PbftOracle: LEADER node CONSENSUS step=%s',state.step)
                  
                elif state.node == _PLINK_ :
                    """
                    just change step of consensus and ignore BlockNew messages; only append them to their logs
                    """
                    if block_num == 0 or signer_id == self._validator_id:
                        # try send PrePrepare for starting consensus in case it's leader block 
                        # use nodes map for checking
                        self._send_pre_prepare(state,block)
                        state.next_step() # => Preparing
                        self.set_consensus_state_for_block_id(block_id,state)
                        LOGGER.debug('PbftOracle: PLINK node CONSENSUS step=%s',state.step)
                elif state.node == _ARBITER_ :
                    """
                    just change step of consensus and ignore BlockNew messages; only append them to their logs
                    wait until plink and leader do first round of consensus
                    """

                    LOGGER.debug('PbftOracle: ARBITER node CONSENSUS step=%s',state.step)
                elif state.node == _AUX_ :
                    """
                    just change step of consensus and ignore BlockNew messages; only append them to their logs
                    and folow decision of plink and leader
                    """
                    LOGGER.debug('PbftOracle: AUX node CONSENSUS step=%s',state.step)
                return True
            elif state.is_step_Ignored or state.is_step_Committing:
                LOGGER.debug('PbftOracle: cant START CONSENSUS for block_id=%s (incorrect state=%s) fail it',_short_id(block_id),state.step)
                #elf._service.fail_block(block.block_id)
                self.cancel_curr_block()
                #self._service.ignore_block(block.block_id)
            else:
                """
                It could be case when NEW BLOCK appeared after PrePrepare request for consensus
                it means that we can choice external or own block for commiting
                """
                
                if _THE_SAME_ID_:
                    """
                    consider this block in consensus 
                    mark it with new_block
                    """ 
                    LOGGER.debug('PbftOracle: NEW BLOCK %s appeared after PrePrepare request!\n',_short_id(block_id))
                    state.set_new_block()
                    self.set_consensus_state_for_block_id(block_id,state)
                else:
                    LOGGER.debug('PbftOracle: NEW BLOCK %s appeared after PrePrepare request IGNORE it !\n',_short_id(block_id))
                    self.cancel_curr_block()

        else:
            LOGGER.debug('PbftOracle: there is no CONSENSUS_STATE for block_id=%s',_short_id(block_id))
            return False

    def check_consensus(self,block):
        block_id = block.block_id.hex()
        #LOGGER.debug("PbftOracle: check_consensus for block='%s'",block_id)
        state = self.get_consensus_state_for_block_id(block,False)
        return state.is_step_Finished if state is not None else False

    def start_view_change(self,state,block):
        """
        
        """
        self._send_viewchange(state,block)
        return True

    def is_canceled(self) :
        return self._canceled

    def cancel_curr_block(self):
        try:
            LOGGER.warning("cancel_curr_block")
            self._service.cancel_block()
            self._canceled = True
        except InvalidState:
            LOGGER.warning("cancel_curr_block: ERR=InvalidState")
            pass

    def ignore_block(self,block):
        block_id = block.block_id.hex()

        state = self.get_consensus_state_for_block_id(block,False)
        state.set_ignored_step()
        self.set_consensus_state_for_block_id(block_id,state)
        LOGGER.warning("PbftOracle: IGNORE block_id=%s => state=%s",_short_id(block_id),state.step)

    def commit_block(self,state,block_id,env):
        LOGGER.debug('%s call commit_block',env)
        if state.unknown_block:
            LOGGER.debug('%s DONT TRY commit_block (UnknownBlock)\n',env)
            return
        elif not state.new_block:
            LOGGER.debug('%s SKIP call commit_block (FOR EXTERNAL BLOCK)\n',env)
            return
        try:
            """
            Do commit only in case we have NEW BLOCK for this block
            if not we just help others node do his consensus
            Check using 'summary' maybe there is another block with more id if so don't do commit for this block
            """
            summary = state.summary
            b_id = block_id.hex()
            sstate = self.get_state_by_summary(summary,"INTO COMMIT_BLOCK")
            commit = True
            if sstate is not None:
                # check previouse commits
                LOGGER.debug('%s state for %s\n',env,_short_id(summary))
                commit = sstate.try_commit(b_id)
                sstate.set_consensus_state_for_block_id(summary,self._consensus_state_store)

            if commit :
                LOGGER.debug('%s do commit for %s\n',env,_short_id(b_id))
                self._service.commit_block(block_id)
            else:
                LOGGER.debug('%s IGNORE commit for %s\n',env,_short_id(b_id))

        except UnknownBlock as err:
            LOGGER.debug('PbftOracle: %s commit_block UnknownBlock err=%s\n',env,err)
        except Exception as err:
            LOGGER.debug('PbftOracle: %s commit_block err=%s\n',env,err)

    def check_block(self,state,block,block_id,env):
        """
        We should check only own block in case block was made as rest-api transaction
        """

        try:
            bid = block.block_id
            summary = block.summary.hex()
            # get state for summary
            s_state = self.get_state_by_summary(summary,"INTO CHECK_BLOCK")

            if not state.new_block:
                # take block id from summary because this is external block corresponding with internal block with same summary
                #summary = block.summary.hex()
                #s_state = self.get_state_by_summary(summary,"CHECK_BLOCK")
                if s_state is not None:
                    bid = s_state.block_id
                    if bid is None:
                         # there is no yet corresponding internal block
                         
                         s_state.set_wait_check()
                         s_state.set_consensus_state_for_block_id(summary,self._consensus_state_store)
                         LOGGER.debug('%s there is no yet corresponding internal block summary=%s WAITING state=%s',env,_short_id(summary),s_state)
                         return False
                    else:
                        LOGGER.debug(' %s use id=%s call check_blocks for %s ',env,_short_id(bid.hex()),_short_id(block_id))
                        self._service.check_blocks([bid])
                        return False

            if s_state is not None and s_state.block_valid(block_id):
                # Already was checked
                LOGGER.debug('%s ALREADY CHECKED block[%s]',env,_short_id(block_id))
                return True
            else:
                LOGGER.debug('PbftOracle: %s call check_blocks [%s]',env,_short_id(block_id))
                self._service.check_blocks([bid])
                return False

        except UnknownBlock:
            LOGGER.debug('PbftOracle: %s UnknownBlock %s',env,_short_id(block_id))
            LOGGER.debug('PbftOracle: %s TRY TO SAY ALREADY CHECKED block=%s and => Committing',env,_short_id(block_id))
            #state.next_step() # => Committing
            #state.set_unknown_block()
            #self.set_consensus_state_for_block_id(block_id,state)
            #self._send_commit(state,block)
            return False

    def get_state_by_summary(self,summary,title):
        state = None
        try:
            state = self._consensus_state_store[summary]
            LOGGER.debug("%s get state=%s",title,state)
        except KeyError:
            LOGGER.debug("%s key=%s error state=UNDEF",title,_short_id(summary))
            pass
        except Exception as ex:
            LOGGER.debug("%s key len=%s",title,len(summary))
            pass
        return state

    def consensus_plink(self,state,msg_type,block,block_id):
        """
        actions for plink nodes
        """
        def is_pre_prepare_valid():
            return True
        LOGGER.debug('PbftOracle: >>> PLINK state=%s',state.step)
        
        if state.is_step_PrePreparing :
            if msg_type == PbftMessageInfo.PRE_PREPARE_MSG:
                
                """
                check PRE_PREPARE_MSG from leader:
                    1) signer_id and summary of block inside PrePrepare match the corresponding fields of the original BlockNew block 
                    2) View in PrePrepare message corresponds to this server's current view &&
                    3) This message hasn't been accepted already with a different summary &&
                    4) Sequence number is within the sequential bounds of the log (low and high water marks)
                """
                if is_pre_prepare_valid():
                    # if correct change step of consensus and send Prepare to All nodes(but only leader will check it)
                    LOGGER.debug('PbftOracle: PLINK PRE_PREPARE_MSG PrePreparing => Preparing')
                    state.next_step() # => Preparing
                    self.set_consensus_state_for_block_id(block_id,state)
                    self._send_prepare(state,block)
                else:
                    # If the PrePrepare is determined to be invalid, then start a view change
                    LOGGER.debug('PbftOracle: PLINK PrePreparing => ViewChange')
                    self.start_view_change()
            else:
                LOGGER.debug('PbftOracle: PLINK PRE_PREPARE_MSG in incorrect consensus state=%s ignore',state.step)

        elif state.is_step_Preparing:
            """
            PREPARING STATE after PrePrepare message
            Check when PREPARED is true
            PREPARED is true for the current node if the following messages are present in its log:
               1) The original BlockNew message
               2) A PrePrepare message matching the original message (in the current view)
               3) 2f + 1 matching Prepare messages from different nodes that match PrePrepare message above (including its own)
            """
            if msg_type == PbftMessageInfo.PREPARE_MSG:
                LOGGER.debug('PbftOracle: PLINK PREPARE_MSG Preparing => Checking')
                state.next_step() # => Checking
                self.set_consensus_state_for_block_id(block_id,state)
                if state.is_own:
                    #  own block - go to the Committing
                    LOGGER.debug('PbftOracle: PLINK skip check_blocks')
                    state.next_step() # => Committing
                    self.set_consensus_state_for_block_id(block_id,state)
                    self._send_commit(state,block)
                    
                else :
                    
                    self._send_prepare(state,block)
                    """
                    check marker maybe block already was checked - in that case go to the commit
                    """
                    if self.check_block(state,block,block_id,'PLINK') :
                        # this external block which is already checked - go to commiting
                        LOGGER.debug('PbftOracle: PLINK ALREADY CHECKED block=%s and => Committing',_short_id(block_id))
                        state.next_step() # => Committing
                        self.set_consensus_state_for_block_id(block_id,state)
                        self._send_commit(state,block)
                        

                #self._send_prepare(state,block)
            else:
                LOGGER.debug('PbftOracle: PLINK NOT PREPARE_MSG in state Preparing ignore')

        elif state.is_step_Checking:
            """
            go to the Committing state for the current node in case if :  
            1) Receive a BlockValid update corresponding to the current working block    
            2) PREPARED is true
            """
            if Message.CONSENSUS_NOTIFY_BLOCK_VALID == msg_type:
                LOGGER.debug('PbftOracle: PLINK have got ValidBlock block_id=%s',_short_id(block_id))
                state.next_step() # => Committing
                self.set_consensus_state_for_block_id(block_id,state)
                self._send_commit(state,block)
                if state.commits:
                    LOGGER.debug('PLINK in state Checking ALREADY HAS COMMIT!')
                    state.next_step() # => Finished
                    self.set_consensus_state_for_block_id(block_id,state)
                    self.commit_block(state,block.block_id,'PLINK')

            else:
                 LOGGER.debug('PbftOracle: PLINK NOT BLOCK_VALID in state Checking IGNORE!')

        elif state.is_step_Committing:
            """
            A BlockValid has been received. Ready to receive Commit messages.
            This node has accepted 2f + 1 Commit messages, including its own
            """
            
            if msg_type == PbftMessageInfo.COMMIT_MSG:
                LOGGER.debug('PbftOracle: PLINK COMMIT_MSG block=%s Committing => Finished!',_short_id(block_id))
                state.next_step() # => Finished
                self.set_consensus_state_for_block_id(block_id,state)
                
                if state.is_own:
                    # own block skip Finished
                    #state.next_step() # => NotInit
                    state.set_commited_step()
                    state.set_published(False)
                    self.set_consensus_state_for_block_id(block_id,state)
                    LOGGER.debug('PbftOracle: PLINK skip commiting')
                    """
                    We should set _published = False
                    """
                else :
                    self.commit_block(state,block.block_id,'PLINK')
                    
            else:
                LOGGER.debug('PbftOracle: PLINK NOT COMMIT_MSG in Committing state!')

        elif state.is_step_Finished:
            """
            This node has accepted 2f + 1 Commit messages, including its own
            """
            if Message.CONSENSUS_NOTIFY_BLOCK_COMMIT == msg_type:
                LOGGER.debug('PbftOracle: PLINK BLOCK_COMMIT block=%s Finished => NotStarted!',_short_id(block_id))
                #state.next_step() # => NotInit
                state.set_commited_step()
                self.set_consensus_state_for_block_id(block_id,state)
                #self.cancel_curr_block()
            else:
                LOGGER.debug('PbftOracle: PLINK IGNORE NOT BLOCK_COMMIT in Finished state !')

        else:
            LOGGER.debug('PbftOracle: PRE_PREPARE_MSG PLINK incorrect consensus state=%s',state.step)
        LOGGER.debug('PbftOracle: <<< PLINK => %s',state.step)

    def consensus_leader(self,state,msg_type,block,block_id):
        """
        actions for LEADER nodes
        """
        LOGGER.debug('>>> LEADER state=%s',state.step)
        if state.is_step_PrePreparing :
            """
            After NewBlock message
            """
            #LOGGER.debug('PbftOracle: LEADER PrePreparing')
            if msg_type == PbftMessageInfo.PREPARE_MSG :
                """
                reply from plink node on PrePrepare message
                we consider PREPARE_MSG as receiving PRE_PREPARE_MSG because we sent it 
                """
                LOGGER.debug('PbftOracle: LEADER PREPARE MSG for block=%s in PrePreparing => Preparing',_short_id(block_id))
                state.next_step() # => Preparing
                self.set_consensus_state_for_block_id(block_id,state)
                LOGGER.debug('PbftOracle: LEADER PrePreparing => %s',state.step)
                self._send_prepare(state,block)
                # skip step 
                state.next_step() # => Checking
                self.set_consensus_state_for_block_id(block_id,state)
                self._service.check_blocks([block.block_id])
            elif msg_type == PbftMessageInfo.PRE_PREPARE_MSG:
                """
                we are owner of this block
                """
                LOGGER.debug('=> PRE_PREPARE LEADER for block=%s in PrePreparing => Preparing',_short_id(block_id))
                state.next_step() # => Preparing
                self.set_consensus_state_for_block_id(block_id,state)
                self._send_prepare(state,block)
            else:
                LOGGER.debug('PbftOracle: LEADER IGNORE NOT PREPARE MSG in state PrePreparing !')

        elif state.is_step_Preparing:
            """
            A PrePrepare message has been received and is valid. Ready to receive Prepare messages corresponding to this PrePrepare

            """
            LOGGER.debug('PbftOracle: LEADER Preparing ')
            if msg_type == PbftMessageInfo.PREPARE_MSG :
                LOGGER.debug('PbftOracle: LEADER have got PREPARE for block=%s in Preparing => Checking',_short_id(block_id))
                self._send_prepare(state,block)
                state.next_step() # => Checking
                self.set_consensus_state_for_block_id(block_id,state)
                if state.is_own:
                    LOGGER.debug('PbftOracle: LEADER skip check_blocks')
                    state.next_step() # => Committing
                    self.set_consensus_state_for_block_id(block_id,state)
                    self._send_commit(state,block)
                else:
                    LOGGER.debug('PbftOracle: LEADER CHECK block=%s and => Checking',_short_id(block_id))
                    
                    self._send_prepare(state,block)
                    """
                    check marker maybe block already was checked - in that case go to the commit
                    """
                    if self.check_block(state,block,block_id,'LEADER') :
                        LOGGER.debug('PbftOracle: LEADER ALREADY CHECKED block=%s and => Committing',_short_id(block_id))
                        state.next_step() # => Committing
                        self.set_consensus_state_for_block_id(block_id,state)
                        self._send_commit(state,block)
                        
                    
            else:
                LOGGER.debug('=> NOT PREPARE_MSG LEADER  in state Preparing IGNORE!')
                
        elif state.is_step_Checking:
            """
            The predicate prepared is true; meaning this node has a BlockNew, a PrePrepare, and 2f + 1 corresponding Prepare messages. Ready to receive a BlockValid update.
            But we should get message from Arbiter 
            """
            
            if Message.CONSENSUS_NOTIFY_BLOCK_VALID == msg_type:
                LOGGER.debug('=> BLOCK_VALID LEADER block_id=%s in Checking => Committing',_short_id(block_id))
                state.next_step() # => Committing
                self.set_consensus_state_for_block_id(block_id,state)
                self._send_commit(state,block)
                if state.commits:
                    # 
                    LOGGER.debug('LEADER in state Checking ALREADY HAS COMMIT!')
                    state.next_step() # => Finished
                    self.set_consensus_state_for_block_id(block_id,state)
                    self.commit_block(state,block.block_id,'LEADER')

            else:
                 LOGGER.debug('=> NOT BLOCK_VALID LEADER in state Checking IGNORE!')

        elif state.is_step_Committing:
            """
            A BlockValid has been received. Ready to receive Commit messages.
            """
            LOGGER.debug('PbftOracle: LEADER in Committing state!')
            if msg_type == PbftMessageInfo.COMMIT_MSG:
                LOGGER.debug('=> COMMIT_MSG LEADER block=%s Committing => Finished!',_short_id(block_id))
                state.next_step() # => Finished
                self.set_consensus_state_for_block_id(block_id,state)
                if state.is_own:
                    # own block skip Finished
                    #state.next_step() # => NotInit
                    state.set_commited_step()
                    state.set_published(False)
                    self.set_consensus_state_for_block_id(block_id,state)
                    LOGGER.debug('PbftOracle: LEADER skip commiting')
                else :
                    self.commit_block(state,block.block_id,'LEADER')
                    
            else:
                LOGGER.debug('=> NOT COMMIT_MSG LEADER in Committing state IGNORE!')
            
        elif state.is_step_Finished:
            """
            The predicate committed is true and the block has been committed to the chain. Ready to receive a BlockCommit update.
            """
            if Message.CONSENSUS_NOTIFY_BLOCK_COMMIT == msg_type:
                LOGGER.debug('=> BLOCK_COMMIT LEADER block=%s Finished => NotStarted!',_short_id(block_id))
                #state.next_step() # => NotInit
                state.set_commited_step()
                self.set_consensus_state_for_block_id(block_id,state)
                #self.cancel_curr_block()

            else:
                LOGGER.debug('PbftOracle: LEADER NOT BLOCK_COMMIT Finished state IGNORE!')

        else:
            LOGGER.debug('PbftOracle: LEADER is incorrect consensus state=%s IGNORE MESSAGE',state.step)
        LOGGER.debug(' <<< LEADER => %s',state.step)
  
    def consensus_aux(self,state,msg_type,block,block_id):
        """
        actions for AUX nodes
        """
        LOGGER.debug('PbftOracle: PREPARE_MSG AUX in state=%s',state.step)
        if state.is_step_PrePreparing :
            pass
        elif state.is_step_Preparing:
            pass
        elif state.is_step_Checking:
            pass
        elif state.is_step_Committing:
            pass
        elif state.is_step_Finished:
            pass
        else:
            LOGGER.debug('PbftOracle: PRE_PREPARE_MSG LEADER incorrect consensus state=%s',state.step)


    def consensus_arbiter(self,state,msg_type,block,block_id):
        """
        actions for ARBITER nodes
        """
        LOGGER.debug('PbftOracle: PREPARE_MSG ARBITER in state=%s',state.step)
        if state.is_step_PrePreparing :
            pass
        elif state.is_step_Preparing:
            pass
        elif state.is_step_Checking:
            """
            The predicate prepared is true; meaning this node has a BlockNew, a PrePrepare, and 2f + 1 corresponding Prepare messages. Ready to receive a BlockValid update.
            Now we can send message to leader
            """
            pass
        elif state.is_step_Committing:
            pass
        elif state.is_step_Finished:
            pass
        else:
            LOGGER.debug('PbftOracle: PRE_PREPARE_MSG ARBITER incorrect consensus state=%s',state.step)

    def consensus_handler(self,state,msg_type,block,block_id):

        LOGGER.debug('PbftOracle: consensus_handler MESSAGE=%s block_id=%s STATE=%s',msg_type,_short_id(block_id),state) 
        if state.node == _PLINK_:
            self.consensus_plink(state,msg_type,block,block_id)
        elif state.node == _LEADER_ :
            self.consensus_leader(state,msg_type,block,block_id)
        elif state.node == _AUX_ :
            self.consensus_aux(state,msg_type,block,block_id)
        elif state.node == _ARBITER_ :
            self.consensus_arbiter(state,msg_type,block,block_id)

    def message_consensus_handler(self,msg_type,block):
        block_id = block.block_id.hex()
        summary  = block.summary.hex()
        
        state = self.get_consensus_state_for_block_id(block,False)

        if state is None:
            """
            Undefined state for block for PrePrepare message 
            We should get state via summary or keep this message using block_id as index 
            """
            #state = self.get_state_by_summary(summary,"PEER_MESSAGE")
            #if state is None:
            """
            This case supposed for PrePrepare 
            we should create state but don't mark them with new_block
            """
            LOGGER.debug('PEER_MESSAGE=%s UNDEFINED state for extern block=%s CREATE NEW ONE',msg_type,_short_id(block_id))
            state = self.get_consensus_state_for_block_id(block)
            state.set_summary(summary)
            state.set_block(block)
            state.next_step() # => PrePreparing
            self.set_consensus_state_for_block_id(block_id,state) # save new state
            estate = self.get_state_by_summary(summary,"BLOCK_VALID")
            if estate is not None:
                estate.set_block(block)
                estate.set_consensus_state_for_block_id(summary,self._consensus_state_store)
                LOGGER.debug('Save block info for summary=%s estate=%s',_short_id(summary),estate)
            else:
                # there is no yet corresponding internal block
                state.set_block(block)
                state.set_consensus_state_for_block_id(summary,self._consensus_state_store)
                LOGGER.debug('Create and save block for summary=%s',_short_id(summary))


        if msg_type == Message.CONSENSUS_NOTIFY_BLOCK_VALID:
            """
            check maybe there is external block which wait this kind of message
            """
            estate = self.get_state_by_summary(state.summary,"BLOCK_VALID")
            if estate is not None:
                # add block_id into valid list
                estate.set_block_valid(block_id)
                estate.set_consensus_state_for_block_id(state.summary,self._consensus_state_store)
                ext_block = estate.block
                if ext_block is not None:
                    wait_check = estate.wait_check
                    estate = self.get_consensus_state_for_block_id(ext_block,False)
                    LOGGER.debug('=> BLOCK_VALID for EXTERNAL block_id=%s NEW_BLOCK=%s state=%s ',_short_id(ext_block.block_id.hex()),estate.new_block,estate) 
                    if estate is not None:
                        if estate.is_step_Checking and not estate.new_block:
                            self.consensus_handler(estate,msg_type,ext_block,ext_block.block_id.hex()) 
                            if not wait_check:
                                return estate.published
                            # else check for own internal block too
                else:
                    LOGGER.debug('There is not ext_block for state=%s ',estate)
        elif msg_type == PbftMessageInfo.COMMIT_MSG:
            # save commit message 
            signer_id = block.signer_id.hex()
            state.add_committer(signer_id)
            state.set_consensus_state_for_block_id(block_id,self._consensus_state_store)
            LOGGER.debug('Save committer=%s for =%s',_short_id(signer_id),_short_id(block_id))


        self.consensus_handler(state,msg_type,block,block_id)
        return state.published

    def peer_message(self,msg):
        """
        consensuse message: PrePrepare, Prepare, Commit, Checkpoint 
        """
        
        p2p_mesg = msg[0]
        payload = PbftMessage()
        payload.ParseFromString(p2p_mesg.content)
        info,block = payload.info,payload.block
        # testing
        #ser = block.SerializeToString()
        #bser = PbftBlockMessage().ParseFromString(ser)
        #LOGGER.debug('PbftOracle: peer_message p2p.content=(%s) bser=%s',type(block),bser)
        msg_type = PbftOracle.CONSENSUS_MSG[info.msg_type]
        block_id = block.block_id.hex()
        summary  = block.summary.hex()
        signer_id = info.signer_id.decode()
        #self.get_state_by_summary(summary,"PEER_MESSAGE")

        LOGGER.debug("PbftOracle: => PEER_MESSAGE %s.'%s' block_id=%s summary=%s signer='%s.%s..%s'",info.seq_num,msg_type,_short_id(block_id),_short_id(summary),self.get_node_type_by_id(signer_id),signer_id[:8],signer_id[-8:])
        return self.message_consensus_handler(info.msg_type,block)

    def _send_pre_prepare(self,state,block):
        # send PRE_PREPARE message 
        messageInfo = PbftMessageInfo(
                    msg_type = PbftMessageInfo.PRE_PREPARE_MSG,
                    view     = 0,
                    seq_num  = state.sequence_number,
                    signer_id = self.get_validator_id().encode()
            ) 
        blockMessage = PbftBlockMessage(
                    block_id  = block.block_id,
                    signer_id =  block.signer_id,
                    block_num = block.block_num,
                    summary   = block.summary 
            )
        self._broadcast(state,PbftMessage(info=messageInfo,block=blockMessage),PbftMessageInfo.PRE_PREPARE_MSG,block.block_id) 

    def _send_prepare(self,state,block):
        # send PREPARE message 
        messageInfo = PbftMessageInfo(
                    msg_type = PbftMessageInfo.PREPARE_MSG,
                    view     = 0,
                    seq_num  = state.sequence_number,
                    signer_id = self.get_validator_id().encode()
            ) 
        blockMessage = PbftBlockMessage(
                    block_id  = block.block_id,
                    signer_id =  block.signer_id,
                    block_num = block.block_num,
                    summary   = block.summary 
            )
        self._broadcast(state,PbftMessage(info=messageInfo,block=blockMessage),PbftMessageInfo.PREPARE_MSG,block.block_id) 

    def _send_commit(self,state,block):
        # send COMMIT message 
        messageInfo = PbftMessageInfo(
                    msg_type = PbftMessageInfo.COMMIT_MSG,
                    view     = 0,
                    seq_num  = state.sequence_number,
                    signer_id = self.get_validator_id().encode()
            ) 
        blockMessage = PbftBlockMessage(
                    block_id  = block.block_id,
                    signer_id =  block.signer_id,
                    block_num = block.block_num,
                    summary   = block.summary 
            )
        self._broadcast(state,PbftMessage(info=messageInfo,block=blockMessage),PbftMessageInfo.COMMIT_MSG,block.block_id) 

    def _send_checkpoint(self,state,block):
        """
        check point message, for log message rotation
        """ 
        messageInfo = PbftMessageInfo(
                    msg_type = PbftMessageInfo.CHECKPOINT_MSG,
                    view     = 0,
                    seq_num  = state.sequence_number,
                    signer_id = self.get_validator_id().encode()
            ) 
        blockMessage = PbftBlockMessage(
                    block_id  = block.block_id,
                    signer_id =  block.signer_id,
                    block_num = block.block_num,
                    summary   = block.summary 
            )
        self._broadcast(state,PbftMessage(info=messageInfo,block=blockMessage),PbftMessageInfo.CHECKPOINT_MSG,block.block_id) 
    
    def _send_viewchange(self,state,block):
        """
        View change message, for when a node suspects the leader node is faulty
        """ 
        messageInfo = PbftMessageInfo(
                    msg_type = PbftMessageInfo.VIEWCHANGE_MSG,
                    view     = -1,
                    seq_num  = state.sequence_number,
                    signer_id = self.get_validator_id().encode()
            ) 
        # TODO add stack of PbftMessage for this block
        self._broadcast(state,PbftViewChange(messageInfo),PbftMessageInfo.VIEWCHANGE_MSG,block.block_id) 

    def _broadcast(self,state,payload,msg_type,block_id):
        # broadcast 
        block_id = block_id.hex()
        state.shift_sequence_number(block_id,self._consensus_state_store)
        mgs_type = PbftOracle.CONSENSUS_MSG[msg_type]
        LOGGER.debug("BROADCAST =>> '%s' for block_id=%s",mgs_type,_short_id(block_id))
        self._service.broadcast(mgs_type,payload.SerializeToString()) 



class PbftBlock:
    def __init__(self, block):
        # fields that come with consensus blocks
        
        self.block_id = block.block_id
        self.previous_id = block.previous_id
        self.signer_id = block.signer_id
        self.block_num = block.block_num
        self.payload = block.payload
        self.summary = block.summary
        #LOGGER.debug('PbftBlock: __init__ block_id=%s prev_id=%s',self.block_id.hex(),self.previous_id.hex())
        # fields that bgt requires
        identifier = block.block_id.hex()
        previous_block_id = block.previous_id.hex()
        signer_public_key = block.signer_id.hex()

        self.identifier = identifier
        self.header_signature = identifier
        self.previous_block_id = previous_block_id
        self.signer_public_key = signer_public_key

        self.header = _DummyHeader(
            consensus=block.payload,
            signer_public_key=signer_public_key,
            previous_block_id=previous_block_id)

        # this is a trick
        self.state_root_hash = block.block_id

    def __str__(self):
        return (
            "Block("
            + ", ".join([
                "block_num: {}".format(self.block_num),
                "block_id: {}".format(_short_id(self.block_id.hex())),
                "previous_id: {}".format(_short_id(self.previous_id.hex())),
                "signer_id: {}".format(_short_id(self.signer_id.hex())), # self.get_node_type_by_id(self.signer_id.hex()),_short_id(self.signer_id.hex())
                "payload: {}".format(self.payload),
                "summary: {}".format(self.summary.hex()),
            ])
            + ")"
        )


class NewBlockHeader:
    '''The header for the block that is to be initialized.'''
    def __init__(self, previous_block, signer_public_key):
        self.consensus = None
        self.signer_public_key = signer_public_key
        self.previous_block_id = previous_block.identifier
        self.block_num = previous_block.block_num + 1


class _DummyHeader:
    def __init__(self, consensus, signer_public_key, previous_block_id):
        self.consensus = consensus
        self.signer_public_key = signer_public_key
        self.previous_block_id = previous_block_id


class _BlockCacheProxy:
    """
    interface to BlockCache
    """
    def __init__(self, service, stream):
        self.block_store = _BlockStoreProxy(service, stream)  # public
        self._service = service

    def __getitem__(self, block_id):
        block_id = bytes.fromhex(block_id)

        try:
            return PbftBlock(self._service.get_blocks([block_id])[block_id])
        except UnknownBlock:
            return None


class _BlockStoreProxy:
    def __init__(self, service, stream):
        self._service = service
        self._stream = stream

    @property
    def chain_head(self):
        return PbftBlock(self._service.get_chain_head())

    def get_block_by_transaction_id(self, transaction_id):
        future = self._stream.send(
            message_type=Message.CLIENT_BLOCK_GET_BY_TRANSACTION_ID_REQUEST,
            content=ClientBlockGetByTransactionIdRequest(
                transaction_id=transaction_id).SerializeToString())

        content = future.result().content

        response = ClientBlockGetResponse()
        response.ParseFromString(content)

        if response.status == ClientBlockGetResponse.NO_RESOURCE:
            raise ValueError("The transaction supplied is not in a block")

        block = response.block

        header = BlockHeader()
        header.ParseFromString(block.header)

        consensus_block = ConsensusBlock(
            block_id=bytes.fromhex(block.header_signature),
            previous_id=bytes.fromhex(header.previous_block_id),
            signer_id=bytes.fromhex(header.signer_public_key),
            block_num=header.block_num,
            payload=header.consensus,
            summary=b'')

        bgt_block = PbftBlock(consensus_block)

        return bgt_block

    def get_block_iter(self, reverse):
        # Ignore the reverse flag, since we can only get blocks
        # starting from the head.

        chain_head = self.chain_head

        yield chain_head

        curr = chain_head

        while curr.previous_id:
            try:
                previous_block = PbftBlock(
                    self._service.get_blocks(
                        [curr.previous_id]
                    )[curr.previous_id])
            except UnknownBlock:
                return

            yield previous_block

            curr = previous_block


class _StateViewFactoryProxy:
    def __init__(self, service):
        self._service = service

    def create_view(self, state_root_hash=None):
        '''The "state_root_hash" is really the block_id.'''

        block_id = state_root_hash

        return _StateViewProxy(self._service, block_id)


class _StateViewProxy:
    def __init__(self, service, block_id):
        self._service = service
        self._block_id = block_id

    def get(self, address):
        try:
            result = self._service.get_state(
                block_id=self._block_id,
                addresses=[address])
        except UnknownBlock:
            LOGGER.debug('_StateViewProxy: UnknownBlock %s\n',self._block_id)
            return None
        return result[address]

    def leaves(self, prefix):
        result = self._service.get_state(
            block_id=self._block_id,
            addresses=[prefix])

        return [
            (address, data)
            for address, data in result.items()
        ]


class _BatchPublisherProxy:
    def __init__(self, stream, signer):
        self.identity_signer = signer  # public
        self._stream = stream

    def send(self, transactions):
        txn_signatures = [txn.header_signature for txn in transactions]

        header = BatchHeader(
            signer_public_key=self.identity_signer.get_public_key().as_hex(),
            transaction_ids=txn_signatures
        ).SerializeToString()

        signature = self.identity_signer.sign(header)

        batch = Batch(
            header=header,
            transactions=transactions,
            header_signature=signature,timestamp=int(time.time()))

        future = self._stream.send(
            message_type=Message.CLIENT_BATCH_SUBMIT_REQUEST,
            content=ClientBatchSubmitRequest(batches=[batch]).SerializeToString())
        LOGGER.debug('_BatchPublisherProxy: future.result ...')
        result = future.result()
        LOGGER.debug('_BatchPublisherProxy: future.result DONE')
        assert result.message_type == Message.CLIENT_BATCH_SUBMIT_RESPONSE
        response = ClientBatchSubmitResponse()
        response.ParseFromString(result.content)
        if response.status != ClientBatchSubmitResponse.OK:
            LOGGER.warning("Submitting batch failed with status %s", response)


def _load_identity_signer(key_dir, key_name):
    """Loads a private key from the key directory, based on a validator's
    identity.

    Args:
        key_dir (str): The path to the key directory.
        key_name (str): The name of the key to load.

    Returns:
        Signer: the cryptographic signer for the key
    """
    key_path = os.path.join(key_dir, '{}.priv'.format(key_name))

    if not os.path.exists(key_path):
        raise Exception("No such signing key file: {}".format(key_path))
    if not os.access(key_path, os.R_OK):
        raise Exception(
            "Key file is not readable: {}".format(key_path))

    LOGGER.info('Loading signing key: %s', key_path)
    try:
        with open(key_path, 'r') as key_file:
            private_key_str = key_file.read().strip()
    except IOError as e:
        raise Exception(
            "Could not load key file: {}".format(str(e)))

    try:
        private_key = Secp256k1PrivateKey.from_hex(private_key_str)
    except signing.ParseError as e:
        raise Exception(
            "Invalid key in file {}: {}".format(key_path, str(e)))

    context = signing.create_context('secp256k1')
    crypto_factory = CryptoFactory(context)
    return crypto_factory.new_signer(private_key)
