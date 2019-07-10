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

from sawtooth_bgt_engine.oracle import BgtOracle, BgtBlock
from sawtooth_bgt_engine.pending import PendingForks
from sawtooth_bgt_common.utils import _short_id

LOGGER = logging.getLogger(__name__)
CHAIN_LEN_FOR_BRANCH = 2 # after this len make a new branch 

class BranchState(object):

    def __init__(self,bid,parent,block_num,service,oracle,ind):
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

    def check_consensus(self,block):
        
        if block.block_num == 2 and self._can_fail_block:
            self._can_fail_block = False
            LOGGER.warning("check_consensus: MAKE BLOCK fail FOR TEST\n")
            return False
        return True

    def check_block(self,block_id):
        # send in case of consensus was reached
        LOGGER.warning("check_block: block_id=%s\n",_short_id(block_id.hex()))
        self._service.check_blocks([block_id])

    def fail_block(self, block_id):
        # send in case of consensus was not reached
        self._service.fail_block(block_id)

    def new_block(self,block):
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
        consensus = b'Devmode' #self._oracle.finalize_block(summary)
        if consensus is None:
            return None

        try:
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
            LOGGER.info('Committing block=%s for BRANCH=%s', _short_id(block.block_id.hex()),self._head_id[:8])
            self.commit_block(block.block_id)
            self._committing = True
            return True
        else:
            LOGGER.info('Ignoring block=%s for BRANCH=%s', _short_id(block.block_id.hex()),self._head_id[:8])
            self.reset_state()
            self.ignore_block(block.block_id)
            return False

    def reset_state(self):
        LOGGER.info('reset_state: for BRANCH[%s]=%s\n', self._ind,self._head_id[:8])
        self._building = False   
        self._published = False  
        self._committing = False

     
        
class BgtEngine(Engine):
    def __init__(self, path_config, component_endpoint):
        # components
        self._branches = {} # for DAG 
        self._new_heads = {}
        self._peers = {}
        self._peers_branches = {}
        self._path_config = path_config
        self._component_endpoint = component_endpoint
        self._service = None
        self._oracle = None
        self._skip   = False
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
        LOGGER.debug('BgtEngine: init done')

    def name(self):
        LOGGER.debug('BgtEngine: ask name')
        return 'Devmode'

    def version(self):
        LOGGER.debug('BgtEngine: ask version')
        return '0.1'

    def stop(self):
        self._exit = True

    def _initialize_block(self,branch=None,new_branch=None):
        LOGGER.debug('BgtEngine: _initialize_block branch[%s]',branch.hex()[:8] if branch is not None else None)
        """
        getting addition chain head for DAG in case call _get_chain_head(parent_head) where parent_head is point for making chain branch
        """
        try:
            # for switch current branch to another node add argument new_branch
            chain_head = self._get_chain_head(branch,new_branch) # get MAIN chain_head. chain_head.block_id is ID of parent's block 
        except exceptions.TooManyBranch:
            LOGGER.debug('BgtEngine: CANT CREATE NEW BRANCH (limit is reached)')
            self._make_branch = False
            return False
        except exceptions.NoChainHead:
            LOGGER.debug('BgtEngine: CANT GET CHAIN HEAD')
            return False
        LOGGER.debug('BgtEngine: _initialize_block ID=%s chain_head=(%s)',_short_id(chain_head.block_id.hex()),chain_head)
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
                LOGGER.debug('BgtEngine: _initialize_block USE Branch[%s]=%s',branch.ind,bid[:8])
            else:
                LOGGER.debug('BgtEngine: _initialize_block NEW Branch[%s]=%s',self._num_branches,bid[:8])
                self._branches[bid] = self.create_branch(bid,parent,block_num)
                self._branches[bid]._try_branch = self._make_branch
                
            
        except exceptions.UnknownBlock:
            LOGGER.debug('BgtEngine: _initialize_block ERROR UnknownBlock')
            #return False
        except exceptions.InvalidState :
            LOGGER.debug('BgtEngine: _initialize_block ERROR InvalidState')
            self._skip = True
            return False
        return True

    def create_branch(self,bid,parent,block_num):
        branch = BranchState(bid,parent,block_num, self._service, self._oracle,self._num_branches)
        self._num_branches += 1
        return branch

    def is_not_build(self):
        for branch in self._branches.values():
            if branch._published and not branch._building:
                return True
        return False
    """
    def _check_consensus(self, block):
        if block.block_num == 2 and self._can_fail_block:
            self._can_fail_block = False
            return False
        return True
        #return self._oracle.verify_block(block)
   

    def _switch_forks(self, current_head, new_head):
        try:
            switch = self._oracle.switch_forks(current_head, new_head)
        # The BGT fork resolver raises TypeErrors in certain cases,
        # e.g. when it encounters non-BGT blocks.
        except TypeError as err:
            switch = False
            LOGGER.warning('BGT fork resolution error: %s', err)

        return switch
    

    """

    def _get_chain_head(self,bid=None,nbid=None):
        return BgtBlock(self._service.get_chain_head(bid,nbid))

    def _get_block(self, block_id):
        return BgtBlock(self._service.get_blocks([block_id])[block_id])

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
        """
        consensus = b'Devmode' #self._oracle.finalize_block(summary)

        if consensus is None:
            return None

        try:
            block_id = self._service.finalize_block(parent_id,consensus)
            LOGGER.info('Finalized summary=%s block_id=%s',summary,_short_id(block_id.hex())) #json.loads(consensus.decode())
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
        """

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
                        LOGGER.debug('BgtEngine: TRY SWITCH BRANCH[%s] (%s->%s)\n',branch.ind,bid[:8],branch._parent_id[:8]) 
                        self._initialize_block(bytes.fromhex(bid),bytes.fromhex(branch._parent_id))
                    else:
                        self._initialize_block(bytes.fromhex(bid))
                else: # already published
                    if self._make_branch and branch._make_branch:
                        # create branch for testing - only one
                        LOGGER.debug('BgtEngine: CREATE NEW BRANCH[%s] (%s)\n',branch.ind,branch._parent_id[:8])
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
                self._published = True
        else: 
            for bid,branch in list(self._branches.items()):
                if not branch._published:
                    if self.start_switch_branch and branch.is_time_to_make_branch:
                        # for testing only - try switch branch
                        LOGGER.debug('BgtEngine: TRY SWITCH BRANCH[%s] (%s->%s)\n',branch.ind,bid[:8],branch._parent_id[:8]) 
                        if self._initialize_block(bytes.fromhex(bid),bytes.fromhex(branch._parent_id)):
                            branch.reset_chain_len()
                            LOGGER.debug('BgtEngine: SWITCHED BRANCH[%s]\n',branch.ind) 
                    else:
                        self._initialize_block(bytes.fromhex(bid))
                else: # already published
                    if self._make_branch and branch.is_time_to_make_branch :
                        # try to create new branch until limit of branch will be reached
                        LOGGER.debug('BgtEngine: TRY CREATE NEW BRANCH[%s] (%s)\n',branch.ind,branch._parent_id[:8])
                        #branch._make_branch = False
                        #self._make_branch = False
                        if self._initialize_block(bytes.fromhex(branch._parent_id)) :
                            branch.reset_chain_len()

                    if False and self._TOTAL_BLOCK == 5:
                        # for testing only - un freeze branch 0 and 
                        (block_id,parent_id) = branch.un_freeze_block()
                        if block_id is not None:
                            self.un_freeze_block(block_id,parent_id)

        if self.is_not_build(): # there is not build one
            self._my_finalize_block()


    def start(self, updates, service, startup_state):
        LOGGER.debug('BgtEngine: start service=%s startup_state=%s.',service,startup_state)
        self._service = service
        self._oracle = BgtOracle(
            service=service,
            component_endpoint=self._component_endpoint,
            config_dir=self._path_config.config_dir,
            data_dir=self._path_config.data_dir,
            key_dir=self._path_config.key_dir)
        self._validator_id = self._oracle.validator_id

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
        LOGGER.debug('BgtEngine: start wait message in %s mode validator=%s.','REAL' if self.is_real_mode else 'TEST',self._validator_id[:8])
        #self._service.initialize_block()
        while True:
            try:
                try:
                    type_tag, data = updates.get(timeout=0.1)
                except queue.Empty:
                    pass
                else:
                    LOGGER.debug('BgtEngine:Received message: %s',Message.MessageType.Name(type_tag))

                    try:
                        handle_message = handlers[type_tag]
                    except KeyError:
                        LOGGER.error('BgtEngine:Unknown type tag: %s',Message.MessageType.Name(type_tag))
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
                LOGGER.exception("BgtEngine:Unhandled exception in message loop")

        LOGGER.debug('BgtEngine: start DONE')
    """
    def _try_to_publish(self):
        if self._published:
            return

        if not self._building:
            if self._initialize_block():
                self._building = True
                LOGGER.debug('BgtEngine: _initialize_block DONE')

        if self._building:
            LOGGER.debug('BgtEngine: _check_publish_block ..')
            if self._check_publish_block():
                LOGGER.debug('BgtEngine: _finalize_block ..')
                block_id = self._finalize_block()
                if block_id:
                    LOGGER.info("Published block %s", _short_id(block_id.hex()))
                    self._published = True
                    self._building = False
                else:
                    LOGGER.debug('BgtEngine: _cancel_block')
                    self._cancel_block()
                    self._building = False
    """
    def un_freeze_block(self,block_id,parent_id):
        self._new_heads[block_id] = parent_id
        LOGGER.info('   NEW_HEAD=%s for BRANCh=%s AFTER FREEZE', block_id[:8],parent_id[:8])

    def _handle_new_block(self, block):
        block = BgtBlock(block)
        block_id = block.block_id.hex()
        signer_id  = block.signer_id.hex()
        LOGGER.info('=> NEW_BLOCK:Received block=%s.%s signer=%s',block.block_num,_short_id(block_id),signer_id[:8])
        if signer_id == self._validator_id:
            # find branch for this block 
            if block.previous_block_id in self._branches:
                branch = self._branches[block.previous_block_id]
                if branch.new_block(block):
                    self._new_heads[block_id] = block.previous_block_id
                    LOGGER.info('   NEW_HEAD=%s for BRANCh=%s', _short_id(block_id),block.previous_block_id[:8])
                else:
                    LOGGER.info('Failed consensus check: %s', _short_id(block_id))
                    # Don't reset now - wait message INVALID_BLOCK
                    #self.reset_state()
        else:
            # external block from another node 
            LOGGER.info('EXTERNAL NEW BLOCK=%s num=%s peer=%s', _short_id(block_id),block.block_num,_short_id(signer_id))
            if block_id not in self._peers_branches:
                branch = self.create_branch('','',block.block_num)
                self._peers_branches[block_id] = branch
                LOGGER.info('START CONSENSUS for BLOCK=%s:%s branch=%s',_short_id(signer_id),_short_id(block_id),branch.ind)
                branch.new_block(block)

    def _handle_valid_block(self, block_id):
        LOGGER.info('=> VALID_BLOCK:Received %s', _short_id(block_id.hex()))
        block = self._get_block(block_id)

        self._pending_forks_to_resolve.push(block)
        self._committing = False
        self._process_pending_forks()
        LOGGER.info('VALID_BLOCK  pending_forks DONE.')

    def _handle_invalid_block(self,block_id):
        
        try:
            block = self._get_block(block_id)
            signer_id  = block.signer_id.hex()
            LOGGER.info('=> INVALID_BLOCK:Received id=%s signer=%s\n', _short_id(block_id.hex()),signer_id[:8])
            if signer_id == self._validator_id:
                if block.previous_block_id in self._branches:
                    branch = self._branches[block.previous_block_id]
                    branch.reset_state()
            else:
                LOGGER.info('=> INVALID_BLOCK: external \n')
                if block_id not in self._peers_branches:
                    branch = self._peers_branches[block_id]
                    branch = self.reset_state()
                    del self._peers_branches[block_id]

        except :
            LOGGER.info('=> INVALID_BLOCK: undefined id=%s\n', _short_id(block_id.hex()))
        self.reset_state()

    def _process_pending_forks(self):
        LOGGER.info('_process_pending_forks ..')
        while not self._committing:
            block = self._pending_forks_to_resolve.pop()
            if block is None:
                break

            self._resolve_fork(block)

    def _resolve_fork(self, block):
        # ask head for branch bid
        bid = block.previous_block_id
        signer_id  = block.signer_id.hex()
        if signer_id == self._validator_id:
            if bid in self._branches:
                chain_head = self._get_chain_head(bytes.fromhex(bid))
                branch = self._branches[bid]
                if branch.resolve_fork(chain_head,block):
                    self._committing = True
                else:
                    self.reset_state()
        else:
            # external block 
            block_id = block.block_id.hex()
            LOGGER.info('EXTERNAL BLOCK=%s num=%s signer=%s', _short_id(block_id),block.block_num,_short_id(signer_id))
            if block_id in self._peers_branches:
                chain_head = self._get_chain_head() # ask main head
                branch = self._peers_branches[block_id] 
                LOGGER.info('RESOLVE FORK for BLOCK=%s:%s branch=%s',_short_id(signer_id),_short_id(block_id),branch.ind)
                if branch.resolve_fork(chain_head,block):
                    self._committing = True
                else:
                    self.reset_state()
                


    def reset_state(self):
        self._building = False   
        #self._published = False  
        self._committing = False 


    def _handle_committed_block(self, block_id):
        block_id = block_id.hex()
        LOGGER.info('=> BLOCK_COMMIT Chain head updated to %s, abandoning block in progress',_short_id(block_id))
        # for DAG new head for branch will be this block_id
        # and we should use it for asking chain head for this branch 
        if block_id in self._new_heads:
            hid = self._new_heads.pop(block_id)
            LOGGER.info('   update chain head for BRANCH=%s->%s',hid[:8],block_id[:8])
            if hid in self._branches:
                branch = self._branches.pop(hid)
                branch.cancel_block(block_id) # change parent_id too 
                branch.reset_state()    
                self._branches[block_id] = branch
                self._TOTAL_BLOCK += 1 
                LOGGER.info('   set new head=%s for BRANCH=%s TOTAL=%s',block_id[:8],hid[:8],self._TOTAL_BLOCK)
        else:
            # external block
            if block_id in self._peers_branches:
                branch = self._peers_branches[block_id]
                branch.cancel_block(block_id) # change parent_id too 
                branch.reset_state()
                del self._peers_branches[block_id] 
                # update _branches
                block = self._get_block(bytes.fromhex(block_id))
                for key,branch in self._branches.items():
                    if branch.block_num == block.block_num:
                        LOGGER.info('   update chain head for BRANCH=%s -> %s',branch.ind,block_id[:8])
                        branch = self._branches.pop(key)
                        branch._parent_id = block_id
                        branch._block_num = block.block_num
                        self._branches[block_id] = branch
                        break
                 
        
        LOGGER.info('=> BLOCK_COMMIT')
        self._process_pending_forks()
        self.reset_state()

    def _handle_peer_connected(self, block):
        #block = BgtBlock(block)
        pinfo = ConsensusNotifyPeerConnected()
        #info = pinfo.ParseFromString(block)
        pid = block.peer_id.hex()
        if pid not in self._peers:
            self._peers[pid] = True
            LOGGER.info('Connected peer with ID=%s\n', _short_id(pid))

    def _handle_peer_message(self, block):
        #block = BgtBlock(block)
        LOGGER.info('_handle_peer_message:Received %s', type(block))

