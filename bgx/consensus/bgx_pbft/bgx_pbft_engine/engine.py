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
import queue

import json

from sawtooth_sdk.consensus.engine import Engine
from sawtooth_sdk.consensus import exceptions
from sawtooth_sdk.protobuf.validator_pb2 import Message

from sawtooth_sdk.protobuf.consensus_pb2 import ConsensusNotifyPeerConnected

from bgx_pbft_engine.oracle import PbftOracle, PbftBlock,_StateViewFactoryProxy
from bgx_pbft_engine.pending import PendingForks
from bgx_pbft_common.protobuf.pbft_consensus_pb2 import PbftMessage,PbftMessageInfo,PbftBlockMessage,PbftViewChange
from bgx_pbft.journal.block_wrapper import NULL_BLOCK_IDENTIFIER
from bgx_pbft_common.utils import _short_id
from enum import Enum

LOGGER = logging.getLogger(__name__)
_CONSENSUS_ = b'pbft'
PBFT_NAME = 'pbft' 
PBFT_VER  = '0.1'
TIMEOUT   = 0.1
PBFT_FULL = True  # full or short mode of PBFT

CHAIN_LEN_FOR_BRANCH = 3 # after this len make a new branch 
CONSENSUS_MSG = ['PrePrepare','Prepare','Commit','CheckPoint']

class Consensus(Enum):
    done = 0
    fail = 1
    pending = 2

class BranchState(object):

    def __init__(self,bid,parent,block_num,service,oracle,validator_id,ind):
        self._head_id = bid
        self._ind = ind
        self._parent_id = parent
        self._block_num = block_num
        self._service = service
        self._oracle  = oracle
        self._committing = False
        self._building   = False
        self._published = True
        self._can_fail_block = False
        # for testing branch
        self._try_branch = True
        self._make_branch = False
        self._freeze_block = None
        self._num_block = 0
        self._chain_len = 0   # for chain lenght
        self._freeze = False # True for freeze block 3
        self._sequence_number = 0
        self._validator_id = validator_id
        LOGGER.debug('BranchState: init branch for %s parent=%s',bid[:8],parent[:8])

    @property
    def ind(self):
        return self._ind

    @property
    def parent(self):
        return self._parent_id

    @property
    def block_num(self):
        return self._block_num

    @property
    def is_time_to_make_branch(self):
        return self._chain_len > CHAIN_LEN_FOR_BRANCH # and self._make_branch

    @property
    def state(self):
        return self._state

    def reset_chain_len(self):
        self._chain_len = 0

    def un_freeze_block(self):
        # for testing only
        block_id,parent_id = None,None
        if self._freeze_block is not None:
            LOGGER.warning("un_freeze_block: un freeze block for BRANCH=%s\n",self._head_id[:8])
            self.check_block(self._freeze_block.block_id) # commit freeze block
            #self.fail_block(self._freeze_block.block_id)  # fail block 
            block_id = self._freeze_block.block_id.hex()
            parent_id = self._freeze_block.previous_block_id
            self._freeze_block = None
        return block_id,parent_id

    def _broadcast(self,payload,msg_type,block_id):
        # broadcast message 
        block_id = block_id.hex()
        #state.shift_sequence_number(block_id,self._consensus_state_store)
        mgs_type = CONSENSUS_MSG[msg_type]
        LOGGER.debug("BROADCAST =>> '%s' for block_id=%s",mgs_type,_short_id(block_id))
        self._service.broadcast(mgs_type,payload.SerializeToString())

    def _make_message(self,block,msg_type):
        messageInfo = PbftMessageInfo(
                    msg_type = msg_type,
                    view     = 0,
                    seq_num  = self._sequence_number,
                    signer_id = bytes.fromhex(self._validator_id)
            ) 
        blockMessage = PbftBlockMessage(
                    block_id  = block.block_id,
                    signer_id =  block.signer_id,
                    block_num = block.block_num,
                    summary   = block.summary 
            )
        return PbftMessage(info=messageInfo,block=blockMessage)

    def _send_pre_prepare(self,block):
        """
        send PRE_PREPARE message 
        """
        message = self._make_message(block,PbftMessageInfo.PRE_PREPARE_MSG)                                                                                                                 
        self._broadcast(message,PbftMessageInfo.PRE_PREPARE_MSG,block.block_id)
        
    def _send_prepare(self,block):
        """
        send PREPARE message 
        """
        message = self._make_message(block,PbftMessageInfo.PREPARE_MSG)                                                                                                                 
        self._broadcast(message,PbftMessageInfo.PREPARE_MSG,block.block_id)

    def _send_commit(self,block):
        """
        send COMMIT message
        """                                                                                                  
        message = self._make_message(block,PbftMessageInfo.COMMIT_MSG)                                                                                                                 
        self._broadcast(message,PbftMessageInfo.COMMIT_MSG,block.block_id) 
    
    def _send_checkpoint(self,block):
        """
        check point message, for log message rotation
        """ 
        message = self._make_message(block,PbftMessageInfo.CHECKPOINT_MSG)
        self._broadcast(message,PbftMessageInfo.CHECKPOINT_MSG,block.block_id) 

    def _send_viewchange(self,block):
        """
        View change message, for when a node suspects the leader node is faulty
        """ 
        message = self._make_message(block,PbftMessageInfo.VIEWCHANGE_MSG)

        self._broadcast(message,PbftMessageInfo.VIEWCHANGE_MSG,block.block_id) 

    def check_consensus(self,block):
        
        if block.block_num == 2 and self._can_fail_block:
            self._can_fail_block = False
            LOGGER.warning("check_consensus: MAKE BLOCK fail FOR TEST\n")
            return False
        return True

    def start_consensus(self,block):
        self._state = 0
        self._send_pre_prepare(block)

    def finish_consensus(self,block,block_id,consensus):
        if self._state == 0:
            # shift to the checking state
            self._state += 1
            LOGGER.warning("finish_consensus:branch[%s] for block_id=%s consensus=%s\n",self._ind,block_id[:8],consensus)
            if consensus:
                # check block and waiting valid or invalid message
                self.check_block(bytes.fromhex(block_id))
            else:
                #self.reset_state()
                self.fail_block(bytes.fromhex(block_id))
        else:
            LOGGER.warning("finish_consensus: IGNORE block_id=%s\n",block_id[:8])

    def check_block(self,block_id):
        # send in case of consensus was reached
        LOGGER.warning("check_block: block_id=%s\n",_short_id(block_id.hex()))
        try:
            self._service.check_blocks([block_id])
        except (exceptions.UnknownBlock,exceptions.ReceiveError):
            LOGGER.warning("check_block: ignore_block block_id=%s\n",_short_id(block_id.hex()))
            self.ignore_block(block_id)
            

    def fail_block(self, block_id):
        # send in case of consensus was not reached
        self._service.fail_block(block_id)

    def new_block(self,block,peers):
        if len(peers) > 0:
            # start consensus for many active peers
            self.start_consensus(block)
            return False

        if self.check_consensus(block):
            # at this point state PREPARED
            LOGGER.info('Passed consensus check in state PREPARED: %s ', _short_id(block.block_id.hex()))
            if block.block_num == 3 and self._try_branch:
                # try make branch pause current block for main branch
                self._make_branch = True
                self._try_branch = False
                if self._freeze:
                    self._freeze_block = block
                else:
                    self.check_block(block.block_id)
            else:
                self.check_block(block.block_id) # this message send chain controller message for continue block validation
                # waiting block valid message
            return True
        else:
            LOGGER.info('Failed consensus blk=%s branch=%s', _short_id(block.block_id.hex()),self._head_id[:8])
            self.reset_state()
            self.fail_block(block.block_id)
            return False
    
    def cancel_block(self,head_id):
        try:
            
            self._service.cancel_block(bytes.fromhex(self._head_id))
            # set new branch HEAD 
            self._head_id = head_id 
            self._num_block += 1 
            self._chain_len += 1
            LOGGER.warning("cancel_block: for branch[%s]=%s NUM HANDLED BLOCKS=%s chain len=%s\n",self._ind,self._head_id[:8],self._num_block,self._chain_len)
        except exceptions.InvalidState:
            LOGGER.warning("cancel_block:  InvalidState\n")
            pass
    
    def commit_block(self, block_id):
        LOGGER.warning("commit_block: block_id=%s\n",_short_id(block_id.hex()))
        self._service.commit_block(block_id)

    def ignore_block(self, block_id):
        # send in case fork was not resolved
        self._service.ignore_block(block_id)

    def finalize_block(self,parent_id,summary):
        consensus = _CONSENSUS_ #self._oracle.finalize_block(summary)
        if consensus is None:
            return None

        try:
            # say to validator that we are ready to finalize this block
            block_id = self._service.finalize_block(parent_id,consensus)
            LOGGER.info('Finalized summary=%s block_id=%s BRANCH=%s',summary,_short_id(block_id.hex()),self._head_id[:8]) 
            self._building = True # ONLY for testing new version - normal True
            self._published = True # ONLY for testing new version- normal True
            # broadcast 
            #LOGGER.debug('broadcast ...')
            #self._service.broadcast('message_type',b'payload')
            return block_id
        except exceptions.BlockNotReady:
            LOGGER.debug('Block not ready to be finalized')
            return None
        except exceptions.InvalidState:
            LOGGER.warning('block cannot be finalized')
            return None

    def switch_forks(self, current_head, new_head):
        try:
            switch = self._oracle.switch_forks(current_head, new_head)
        # The BGT fork resolver raises TypeErrors in certain cases,
        # e.g. when it encounters non-BGT blocks.
        except TypeError as err:
            switch = False
            LOGGER.warning('BGT fork resolution error: %s', err)

        return switch

    def resolve_fork(self,chain_head,block):
        LOGGER.info('Branch[%s] Choosing between chain heads current:%s new:%s',self._head_id[:8],_short_id(chain_head.block_id.hex()),_short_id(block.block_id.hex()))
        if self.switch_forks(chain_head, block):
            """
            for full version shift into commiting state
            for short we can commit right now
            """
            if PBFT_FULL:
                # broadcast commit message and shift into commiting state
                self._state += 1 
                self._send_commit(block)
                return Consensus.pending
            else:
                LOGGER.info('Committing block=%s for BRANCH=%s', _short_id(block.block_id.hex()),self._head_id[:8])
                self.commit_block(block.block_id)
                self._committing = True
                return Consensus.done
        else:
            LOGGER.info('Ignoring block=%s for BRANCH=%s', _short_id(block.block_id.hex()),self._head_id[:8])
            self.reset_state()
            self.ignore_block(block.block_id)
            return Consensus.fail

    def reset_state(self):
        LOGGER.info('reset_state: for BRANCH[%s]=%s\n', self._ind,self._head_id[:8])
        self._building = False   
        self._published = False  
        self._committing = False
        self._state = 0
        self._sequence_number = 0

    def __str__(self):
        return "{} (block_num:{}, state:{})".format(
            self.parent[:8],
            self.block_num,
            self.state,
            
        )
     
        
class PbftEngine(Engine):
    def __init__(self, path_config, component_endpoint,pbft_config=None):
        # components
        self._branches = {} # for DAG 
        self._new_heads = {}
        self._peers = {}
        self._peers_branches = {}
        self._pre_prepare_msgs = {} # for aggregating blocks by summary 
        self._prepare_msgs = {}
        self._path_config = path_config
        self._component_endpoint = component_endpoint
        self._service = None
        self._oracle = None
        self._skip   = False
        self._chain_head = None
        # state variables
        self._exit = False
        self._published = False
        self._building = False
        self._committing = False
        self._can_fail_block = False #True #False # True for testing
        self._make_branch = True
        self._TOTAL_BLOCK = 0
        self._pending_forks_to_resolve = PendingForks()
        self._num_branches = 0 #
        LOGGER.debug('PbftEngine: init done')

    def name(self):
        LOGGER.debug('PbftEngine: ask name=%s',PBFT_NAME)
        return PBFT_NAME

    def version(self):
        LOGGER.debug('PbftEngine: ask version=%s ',PBFT_VER)
        return PBFT_VER

    def stop(self):
        self._exit = True

    def get_chain_settings(self):
        # get setting from chain
        LOGGER.debug('get_chain_settings HEAD=%s',self._chain_head)

    def _initialize_block(self,branch=None,new_branch=None,is_new = False):
        LOGGER.debug('PbftEngine: _initialize_block branch[%s] is_new=%s',branch.hex()[:8] if branch is not None else None,is_new)
        """
        getting addition chain head for DAG in case call _get_chain_head(parent_head) where parent_head is point for making chain branch
        """
        try:
            # for switch current branch to another node add argument new_branch
            chain_head = self._get_chain_head(branch,new_branch,is_new) # get MAIN chain_head. chain_head.block_id is ID of parent's block 
            if not self._chain_head:
                self._chain_head = chain_head
        except exceptions.TooManyBranch:
            LOGGER.debug('PbftEngine: CANT CREATE NEW BRANCH (limit is reached)')
            self._make_branch = False
            return False
        except exceptions.NoChainHead:
            # head was updated or not commited yet
            LOGGER.debug('PbftEngine: CANT GET CHAIN HEAD for=%s',branch.hex()[:8] if branch is not None else None)
            return False
        LOGGER.debug('PbftEngine: _initialize_block ID=%s chain_head=(%s)',_short_id(chain_head.block_id.hex()),chain_head)
        #initialize = True #self._oracle.initialize_block(chain_head)

        #if initialize:
        try:
            self._service.initialize_block(previous_id=chain_head.block_id)
            # for remove this branch to another point 
            bid = branch.hex() if branch is not None else chain_head.block_id.hex()
            parent = chain_head.previous_block_id
            block_num = chain_head.block_num 
            if bid in self._branches:
                #branch = self._branches[bid]
                
                branch = self._branches[bid]
                branch._published = True
                branch._parent_id = parent
                branch._block_num = block_num
                if new_branch is not None :
                    del self._branches[bid]
                    self._branches[new_branch.hex()] = branch 
                LOGGER.debug('PbftEngine: _initialize_block USE Branch[%s]=%s',branch.ind,bid[:8])
            else:
                LOGGER.debug('PbftEngine: _initialize_block NEW Branch[%s]=%s',self._num_branches,bid[:8])
                self._branches[bid] = self.create_branch(bid,parent,block_num)
                self._branches[bid]._try_branch = self._make_branch
                
            
        except exceptions.UnknownBlock:
            LOGGER.debug('PbftEngine: _initialize_block ERROR UnknownBlock')
            #return False
        except exceptions.InvalidState :
            LOGGER.debug('PbftEngine: _initialize_block ERROR InvalidState')
            self._skip = True
            return False
        except Exception as ex:
            LOGGER.debug('PbftEngine: _initialize_block HEAD=%s.%s ERROR %s!!!\n',chain_head.block_num,chain_head.block_id.hex()[:8],ex)
            return False

        return True

    def create_branch(self,bid,parent,block_num):
        branch = BranchState(bid, parent, block_num, self._service, self._oracle, self._validator_id,self._num_branches)
        self._num_branches += 1
        return branch

    def is_not_build(self):
        for branch in self._branches.values():
            if branch._published and not branch._building:
                return True
        return False

    def _get_chain_head(self,bid=None,nbid=None,is_new=False):
        return PbftBlock(self._service.get_chain_head(bid,nbid,is_new))

    def _get_block(self, block_id):
        return PbftBlock(self._service.get_blocks([block_id])[block_id])

    def _summarize_block(self):
        try:
            return self._service.summarize_block()
        except exceptions.InvalidState as err:
            LOGGER.warning(err)
            return None,None
        except exceptions.BlockNotReady:
            #LOGGER.debug('exceptions.BlockNotReady')
            return None,None


    def _my_finalize_block(self):
        """
        in case DAG we should return parent for block which is ready  
        because we ask one of the initialized blocks
        """
        summary,parent_id = self._summarize_block()

        if summary is None:
            #LOGGER.debug('Block not ready to be summarized')
            return None
        bid = parent_id.hex()
        LOGGER.debug('Can FINALIZE NOW parent=%s branches=%s',_short_id(bid),[key[:8] for key in self._branches.keys()])
        if bid in self._branches:
            LOGGER.debug('FINALIZE BRANCH=%s',bid[:8])
            branch = self._branches[bid]
            branch.finalize_block(parent_id,summary)
        
    def _check_publish_block(self):
        # Publishing is based solely on wait time, so just give it None.
        LOGGER.debug('_check_publish_block ')
        return self._oracle.check_publish_block(None)

    def _testing_mode(self):
        # testing mode consensus
        if not self._published :
            # FIRST publish
            if not self._skip and self._initialize_block() :  
                self._published = True
        else: 
            for bid,branch in list(self._branches.items()):
                if not branch._published:
                    if self._TOTAL_BLOCK == 5 and branch.ind > 0:
                        # for testing only - try switch branch
                        LOGGER.debug('PbftEngine: TRY SWITCH BRANCH[%s] (%s->%s)\n',branch.ind,bid[:8],branch._parent_id[:8]) 
                        self._initialize_block(bytes.fromhex(bid),bytes.fromhex(branch._parent_id))
                    else:
                        self._initialize_block(bytes.fromhex(bid))
                else: # already published
                    if self._make_branch and branch._make_branch:
                        # create branch for testing - only one
                        LOGGER.debug('PbftEngine: CREATE NEW BRANCH[%s] (%s)\n',branch.ind,branch._parent_id[:8])
                        branch._make_branch = False
                        self._make_branch = False
                        self._initialize_block(bytes.fromhex(branch._parent_id))
                    if self._TOTAL_BLOCK == 5:
                        # for testing only - un freeze branch 0 and 
                        (block_id,parent_id) = branch.un_freeze_block()
                        if block_id is not None:
                            self.un_freeze_block(block_id,parent_id)

        if self.is_not_build(): # there is not build one
            self._sum_cnt += 1
            if self._sum_cnt > 10:
                self._sum_cnt = 0
                self._my_finalize_block()

    @property
    def start_switch_branch(self):
        return not self._make_branch and len(self._branches) > 1

    def _real_mode(self):
        # real mode consensus
        if not self._published :
            # FIRST publish
            if not self._skip and self._initialize_block() :  
                # at this point we can ask settings via chain using initial chain_head state_hash 
                self.get_chain_settings()
                self._published = True
        else: 
            for bid,branch in list(self._branches.items()):
                if not branch._published:
                    if self.start_switch_branch and branch.is_time_to_make_branch:
                        # for testing only - try switch branch
                        LOGGER.debug('PbftEngine: TRY SWITCH BRANCH[%s] (%s->%s)\n',branch.ind,bid[:8],branch._parent_id[:8]) 
                        if self._initialize_block(bytes.fromhex(bid),bytes.fromhex(branch._parent_id)):
                            branch.reset_chain_len()
                            LOGGER.debug('PbftEngine: SWITCHED BRANCH[%s]\n',branch.ind) 
                    else:
                        # try to do new branch 
                        if self._make_branch and branch.is_time_to_make_branch :
                            # try to create new branch until limit of branch will be reached
                            LOGGER.debug('PbftEngine: TRY1 CREATE NEW BRANCH[%s] (%s)\n',branch.ind,branch._parent_id[:8])
                            #branch._make_branch = False
                            #self._make_branch = False
                            if self._initialize_block(bytes.fromhex(branch._parent_id),is_new=True) :
                                branch.reset_chain_len()
                        self._initialize_block(bytes.fromhex(bid))
                else: # already published
                    if self._make_branch and branch.is_time_to_make_branch :
                        # try to create new branch until limit of branch will be reached
                        LOGGER.debug('PbftEngine: TRY CREATE NEW BRANCH[%s] (%s)\n',branch.ind,branch._parent_id[:8])
                        #branch._make_branch = False
                        #self._make_branch = False
                        #if self._initialize_block(bytes.fromhex(branch._parent_id),is_new=True) :
                        #    branch.reset_chain_len()

                    if False and self._TOTAL_BLOCK == 5:
                        # for testing only - un freeze branch 0 and 
                        (block_id,parent_id) = branch.un_freeze_block()
                        if block_id is not None:
                            self.un_freeze_block(block_id,parent_id)

        if self.is_not_build(): # there is not build one
            self._my_finalize_block()


    def start(self, updates, service, startup_state):
        LOGGER.debug('PbftEngine: start service=%s startup_state=%s.',service,startup_state)
        self._service = service
        self._state_view_factory = _StateViewFactoryProxy(service)
        self._oracle = PbftOracle(
            service=service,
            component_endpoint=self._component_endpoint,
            config_dir=self._path_config.config_dir,
            data_dir=self._path_config.data_dir,
            key_dir=self._path_config.key_dir)
        self._validator_id = self._oracle.validator_id
        self._dag_step = self._oracle.dag_step
        CHAIN_LEN_FOR_BRANCH = self._dag_step

        # 1. Wait for an incoming message.
        # 2. Check for exit.
        # 3. Handle the message.
        # 4. Check for publishing.
        
        handlers = {
            Message.CONSENSUS_NOTIFY_BLOCK_NEW: self._handle_new_block,
            Message.CONSENSUS_NOTIFY_BLOCK_VALID: self._handle_valid_block,
            Message.CONSENSUS_NOTIFY_BLOCK_INVALID : self._handle_invalid_block,
            Message.CONSENSUS_NOTIFY_BLOCK_COMMIT:self._handle_committed_block,
            Message.CONSENSUS_NOTIFY_PEER_CONNECTED:self._handle_peer_connected,
            Message.CONSENSUS_NOTIFY_PEER_MESSAGE:self._handle_peer_message,
            #CONSENSUS_NOTIFY_PEER_DISCONNECTED 
        }
        self._sum_cnt = 0
        self.is_real_mode = True
        LOGGER.debug('PbftEngine: start wait message in %s mode validator=%s dag_step=%s.','REAL' if self.is_real_mode else 'TEST',self._validator_id[:10],self._dag_step)
        #self._service.initialize_block()
        while True:
            try:
                try:
                    type_tag, data = updates.get(timeout=TIMEOUT)
                except queue.Empty:
                    pass
                else:
                    LOGGER.debug('PbftEngine:Received message: %s',Message.MessageType.Name(type_tag))

                    try:
                        handle_message = handlers[type_tag]
                    except KeyError:
                        LOGGER.error('PbftEngine:Unknown type tag: %s',Message.MessageType.Name(type_tag))
                    else:
                        handle_message(data)

                if self._exit:
                    break

                #self._try_to_publish()
                if self.is_real_mode:
                    self._real_mode()
                else:
                    self._testing_mode()

            except Exception:  # pylint: disable=broad-except
                LOGGER.exception("PbftEngine:Unhandled exception in message loop")

        LOGGER.debug('PbftEngine: start DONE')

    def un_freeze_block(self,block_id,parent_id):
        self._new_heads[block_id] = parent_id
        LOGGER.info('   NEW_HEAD=%s for BRANCh=%s AFTER FREEZE', block_id[:8],parent_id[:8])

    def check_consensus(self,blocks,block_num,summary,num_peers):
        # check maybe all messages arrived  
        if len(blocks) == (num_peers + 1):                                                                                                                                
            selected = max(blocks.items(), key = lambda x: x[0])[0]                                                                                                       
            LOGGER.debug("We have all prepares for block=%s SUMMARY=%s select=%s blocks=%s",block_num,summary[:8],selected[:8],[key[:8] for key in blocks.keys()])        
            LOGGER.debug("COMMIT BLOCK=%s",selected[:8])                                                                                                                  
            # send prepare again                                                                                                                                          
            #self._peers_branches[selected]._send_prepare(block)
            if selected in self._pre_prepare_msgs:
                """
                free PRE_PREPARE mess here. Now we have new_block and will ignore PRE_PREPARE
                """
                self._pre_prepare_msgs.pop(selected)
            """
            AT THIS POINT WE CAN START PBFT FOR SELECTED BLOCK
            we choice only one block from all peer's blocks and fail the rest of them 
            for simple version of consensus we can say commit right now
            """                                                                                                          
            self._peers_branches[selected].finish_consensus(None,selected,True)                                                                                           
            for bid in blocks.keys():                                                                                                                                     
                if bid != selected:                                                                                                                                       
                    LOGGER.debug("FAIL BLOCK=%s",bid[:8])                                                                                                                 
                    #self._peers_branches[bid]._send_prepare(block) 
                    if bid in self._pre_prepare_msgs:
                        self._pre_prepare_msgs.pop(bid)
                    self._peers_branches[bid].finish_consensus(None,bid,False)                                                                                            
                    # drop list for summary                                                                                                                               
            self._prepare_msgs.pop(summary)                                                                                                                               
            LOGGER.debug("=>ALL SUMMARY=%s\n",[key[:8] for key in self._prepare_msgs.keys()])                                                                             


    def _handle_new_block(self, block):
        block = PbftBlock(block)
        block_id = block.block_id.hex()
        signer_id  = block.signer_id.hex()
        summary = block.summary.hex()
        block_num = block.block_num
        num_peers = len(self._peers) 
        LOGGER.info('=> NEW_BLOCK:Received block=%s.%s signer=%s summ=%s',block_num,_short_id(block_id),signer_id[:8],summary[:8])
        def check_consensus():
            if num_peers > 0 and summary in self._prepare_msgs:                                                                                                                   
                blocks = self._prepare_msgs[summary]
                self.check_consensus(blocks,block_num,summary,num_peers)

        if signer_id == self._validator_id:
            # find branch for this block 
            if block.previous_block_id in self._branches:
                branch = self._branches[block.previous_block_id]
                self._peers_branches[block_id] = branch # add ref on branch for own block 
                result =  branch.new_block(block,self._peers)
                if result == Consensus.done:
                    # refer for block on branch
                    self._new_heads[block_id] = block.previous_block_id
                    LOGGER.info('   NEW_HEAD=%s for BRANCh=%s', block_id[:8],block.previous_block_id[:8])
                elif result == Consensus.fail:
                    LOGGER.info('Failed consensus check: %s', block_id[:8])
                else:
                    LOGGER.info('consensus started for block=%s->%s', block_id[:8],block.previous_block_id[:8])
                    self._new_heads[block_id] = block.previous_block_id
                    if block_id in self._pre_prepare_msgs:
                        """
                        free PRE_PREPARE mess here. Now we have new_block and will ignore PRE_PREPARE
                        """
                        msg = self._pre_prepare_msgs[block_id] # self._pre_prepare_msgs.pop(block_id)
                        branch._send_prepare(msg)

                    check_consensus()
                    # Don't reset now - wait message INVALID_BLOCK
                    #self.reset_state()
        else:
            # external block from another node 
            
            if block_id not in self._peers_branches:
                LOGGER.info('EXTERNAL NEW BLOCK=%s.%s peer=%s',block_num, _short_id(block_id),_short_id(signer_id))
                branch = self.create_branch('','',block_num)
                self._peers_branches[block_id] = branch
                LOGGER.info('START CONSENSUS for BLOCK=%s(%s) branch=%s',_short_id(block_id),signer_id[:8],branch.ind)
                branch.new_block(block,self._peers)
                self._new_heads[block_id] = block.previous_block_id
                LOGGER.info('   NEW_HEAD=%s for BRANCh=%s', block_id[:8],block.previous_block_id[:8])
                if block_id in self._pre_prepare_msgs:
                    """
                    free PRE_PREPARE mess here. Now we have new_block and will ignore PRE_PREPARE
                    """
                    msg = self._pre_prepare_msgs[block_id] # self._pre_prepare_msgs.pop(block_id)
                    branch._send_prepare(msg)
                # check maybe all messages arrived
                check_consensus()
            else:
                LOGGER.info('EXTERNAL BLOCK=%s.%s num=%s peer=%s IGNORE(already has)', block_num,_short_id(block_id),_short_id(signer_id))
                


    def _handle_valid_block(self, block_id):
        """
        this is answer on check_block
        """
        LOGGER.info('=> VALID_BLOCK:Received %s', _short_id(block_id.hex()))
        block = self._get_block(block_id)

        self._pending_forks_to_resolve.push(block)
        self._committing = False
        self._process_pending_forks()
        LOGGER.info('VALID_BLOCK  pending_forks DONE.')

    def _handle_invalid_block(self,block_id):
        """
        this is answer on check_block
        """
        try:
            block = self._get_block(block_id)
            signer_id  = block.signer_id.hex()
            bid = block_id.hex()
            LOGGER.info('=> INVALID_BLOCK:Received id=%s signer=%s\n', _short_id(bid),signer_id[:8])
            if bid in self._new_heads:
                self._new_heads.pop(bid)
            if signer_id == self._validator_id:
                if block.previous_block_id in self._branches:
                    branch = self._branches[block.previous_block_id]
                    if bid in self._peers_branches:
                        del self._peers_branches[bid]
                    if block.block_num == 0:
                        branch.reset_state()
                    else:
                        LOGGER.info('=> INVALID_BLOCK: DONT DO reset \n')
            else:
                LOGGER.info('=> INVALID_BLOCK: external block=%s branches=%s \n',bid[:8],[key[:8] for key in self._peers_branches.keys()])
                if bid in self._peers_branches:
                    branch = self._peers_branches[bid]
                    branch = self.reset_state()
                    del self._peers_branches[bid]
            LOGGER.info('=> INVALID_BLOCK: branches=%s \n',[key[:8] for key in self._peers_branches.keys()])
        except :
            LOGGER.info('=> INVALID_BLOCK: undefined id=%s\n', _short_id(block_id.hex()))
        self.reset_state()

    def _process_pending_forks(self):
        LOGGER.info('_process_pending_forks commiting=%s.',self._committing)
        while not self._committing:
            block = self._pending_forks_to_resolve.pop()
            if block is None:
                break

            self._resolve_fork(block)

    def _resolve_fork(self, block):
        # ask head for branch bid
        bid = block.previous_block_id
        bbid = bytes.fromhex(bid)
        signer_id  = block.signer_id.hex()
        block_id = block.block_id.hex()

        def resolve_fork(branch,chain_head,block):
            # resolve this fork
            LOGGER.info('RESOLVE FORK for BLOCK=%s(%s) branch=%s',_short_id(block_id),signer_id[:8],branch.ind)
            result = branch.resolve_fork(chain_head,block)
            if result == Consensus.done:
                self._committing = True
            elif result == Consensus.fail:
                self.reset_state()
            else:
                # pending start commiting
                LOGGER.info('START COMMITING for BLOCK=%s(%s)',_short_id(block_id),signer_id[:8])

        if signer_id == self._validator_id:
            if bid in self._branches:
                # head could be already changed - we can get new head for this branch
                chain_head = self._get_chain_head(bbid)
                branch = self._branches[bid]
                resolve_fork(branch,chain_head,block)
            else:
                LOGGER.info('HEAD FOR BLOCK=%s(%s) was changed',block.block_num, _short_id(block_id),signer_id[:8])
        else:
            # external block 
            LOGGER.info('EXTERNAL BLOCK=%s(%s) num=%s prev=%s', _short_id(block_id),signer_id[:8],block.block_num,bid[:8])
            if block_id in self._peers_branches:
                # head could be already changed - we can get new head for this branch
                chain_head = self._get_chain_head(None if bid == NULL_BLOCK_IDENTIFIER else bbid) # ask head for branch
                branch = self._peers_branches[block_id] 
                resolve_fork(branch,chain_head,block)
                


    def reset_state(self):
        self._building = False   
        #self._published = False  
        self._committing = False 


    def _handle_committed_block(self, block_id):
        block_id = block_id.hex()
        

        def _update_head_branch(prev_num,block_num):
            LOGGER.info('   _update_head_branch check=%s',prev_num)
            for key,branch in self._branches.items():
                if branch.block_num == prev_num:
                    LOGGER.info('   update chain head for BRANCH=%s -> %s',branch.ind,block_id[:8])
                    branch = self._branches.pop(key)
                    branch._parent_id = block_id
                    branch._block_num = block_num
                    self._branches[block_id] = branch
                    return True
            return False

        LOGGER.info('=> BLOCK_COMMIT Chain head updated to %s, abandoning block in progress heads=%s',_short_id(block_id),[key[:8] for key in self._new_heads.keys()])
        # for DAG new head for branch will be this block_id
        # and we should use it for asking chain head for this branch 
        if block_id in self._new_heads:
            hid = self._new_heads.pop(block_id) # hid is parent of this block
            LOGGER.info('   update chain head for BRANCH=%s->%s branches=%s+%s',hid[:8],block_id[:8],[key[:8] for key in self._branches.keys()],[key[:8] for key in self._peers_branches.keys()])
            if hid in self._branches:
                branch = self._branches.pop(hid)
                branch.cancel_block(block_id) # change parent_id too 
                branch.reset_state()    
                self._branches[block_id] = branch
                self._TOTAL_BLOCK += 1 
                if block_id in self._peers_branches:
                    del self._peers_branches[block_id]
                LOGGER.info('   set new head=%s for BRANCH=%s TOTAL=%s peers branches=%s',block_id[:8],hid[:8],self._TOTAL_BLOCK,[key[:8] for key in self._peers_branches.keys()])
            else:
                # external block
                LOGGER.info('head updated for=%s  peers branches=%s',_short_id(block_id),[key[:8] for key in self._peers_branches.keys()])
                if block_id in self._peers_branches:
                    branch = self._peers_branches[block_id]
                    branch.cancel_block(block_id) # change parent_id too 
                    branch.reset_state()
                    del self._peers_branches[block_id] 
                    # update _branches
                    block = self._get_block(bytes.fromhex(block_id))
                    prev = block
                    while not _update_head_branch(prev.block_num,block.block_num):
                        prev = self._get_block(bytes.fromhex(prev.previous_block_id))

        
        LOGGER.info('=> BLOCK_COMMIT prepre=%s pre=%s branches=%s+%s',len(self._pre_prepare_msgs),len(self._prepare_msgs),[key[:8] for key in self._branches.keys()],[key[:8] for key in self._peers_branches.keys()])
        self._process_pending_forks()
        self.reset_state()

    def _handle_peer_connected(self, block):
        #block = PbftBlock(block)
        pinfo = ConsensusNotifyPeerConnected()
        #info = pinfo.ParseFromString(block)
        pid = block.peer_id.hex()
        if pid not in self._peers and pid != self._validator_id:
            self._peers[pid] = True
            LOGGER.info('Connected peer with ID=%s\n', _short_id(pid))

    def _handle_peer_message(self, msg):
        """
        consensuse message: PrePrepare, Prepare, Commit, Checkpoint 
        """
        
        p2p_mesg = msg[0]
        payload = PbftMessage()
        payload.ParseFromString(p2p_mesg.content)
        info,block = payload.info,payload.block
        msg_type = info.msg_type
        block_id = block.block_id.hex()
        signer_id = block.signer_id.hex()
        summary  = block.summary.hex()
        peer_id = info.signer_id.hex()
        block_num = block.block_num
        LOGGER.debug("=> PEER_MESSAGE %s.'%s' block_id=%s(%s) summary=%s peer=%s",info.seq_num,CONSENSUS_MSG[msg_type],block_id[:8],signer_id[:8],summary[:8],peer_id[:8])
        if msg_type == PbftMessageInfo.PRE_PREPARE_MSG:
            # send reply 
            LOGGER.debug("=>SEND PREPARE for block=%s branches=%s+%s",block_id[:8],[key[:8] for key in self._branches.keys()],[key[:8] for key in self._peers_branches.keys()])
            if block_id in self._branches:
                self._branches[block_id]._send_prepare(block)
            elif block_id in self._peers_branches:
                self._peers_branches[block_id]._send_prepare(block)
            elif block_id not in self._pre_prepare_msgs:
                # message arrive before corresponding block appeared save block part of message
                LOGGER.debug("=>message arrive before corresponding BLOCK=%s appeared - SAVE\n",block_id[:8])
                self._pre_prepare_msgs[block_id] = block  

        elif msg_type == PbftMessageInfo.PREPARE_MSG:
            # continue consensus 
            LOGGER.debug("=>PREPARE for block=%s branches=%s+%s",block_id[:8],[key[:8] for key in self._branches.keys()],[key[:8] for key in self._peers_branches.keys()])
            if block_id in self._peers_branches:
                """
                it really means that NEW_BLOCK message already appeared
                """
                if block_num == 0:
                    self._peers_branches[block_id].finish_consensus(block,block_id,True)
                else:
                    if self._peers_branches[block_id].state > 0:
                        # skip message after commit or fail
                        return
                    # waiting until all block with equivalent summary will have prepare message
                    LOGGER.debug("=>CHECK SUMMARY=%s ALL=%s",summary[:10],[key[:8] for key in self._prepare_msgs.keys()])
                    if summary in self._prepare_msgs:
                        #  add block for summary list
                        blocks = self._prepare_msgs[summary]
                        LOGGER.debug("=>SUMMARY=%s have blocks=%s",summary[:10],[key[:8] for key in blocks.keys()])
                        if block_id in blocks:
                            LOGGER.debug("=>IGNORE BLOCK=%s FOR SUMMARY=%s (already has).",block_id[:8],summary[:8])
                        else:
                            # add block into list and check number of blocks
                            num_peers = len(self._peers)
                            blocks[block_id] = True
                            LOGGER.debug("=>ADD BLOCK=%s INTO SUMMARY=%s total=%s peers=%s",block_id[:8],summary[:8],len(blocks),num_peers) 
                            self.check_consensus(blocks,block_num,summary,num_peers)
                            
                    else:
                        LOGGER.debug("=>ADD BLOCK=%s INTO SUMMARY=%s",block_id[:8],summary[:8])
                        self._prepare_msgs[summary] = {block_id : True}
            else:
                """
                there is no NEW_BLOCK message yet but save message
                """ 
                if summary in self._prepare_msgs:
                    # already into prepare - we can add info about this block in case it new 
                    blocks = self._prepare_msgs[summary]
                    LOGGER.debug("=>SUMMARY=%s have blocks=%s (no block yet)",summary[:10],[key[:8] for key in blocks.keys()])
                    if block_id not in blocks:
                         LOGGER.debug("=>ADD BLOCK=%s INTO SUMMARY=%s total=%s (no block yet)",block_id[:8],summary[:8],len(blocks))
                         blocks[block_id] = True
                    
                else:
                    # first prepare message for this block 
                    if block_id in self._pre_prepare_msgs:
                        # only after PRE_PREPARE - in case PRE_PREPARE missing - block was commited
                        LOGGER.debug("=>ADD BLOCK=%s INTO SUMMARY=%s (no block yet)",block_id[:8],summary[:8])
                        self._prepare_msgs[summary] = {block_id : True}
        elif msg_type == PbftMessageInfo.COMMIT_MSG:
            """
            commiting state 
            """
            LOGGER.debug("=>COMMIT for block=%s branches=%s+%s",block_id[:8],[key[:8] for key in self._branches.keys()],[key[:8] for key in self._peers_branches.keys()])
            if block_id in self._peers_branches:
                branch = self._peers_branches[block_id]
                LOGGER.debug("=>COMMIT for block=%s peer branch=%s",block_id[:8],branch)
            elif block_id in self._branches:
                branch = self._branches[block_id]
                LOGGER.debug("=>COMMIT for block=%s branch=%s",block_id[:8],branch)

