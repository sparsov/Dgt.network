# Copyright NTRLab 2019
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

from abc import ABCMeta
from abc import abstractmethod
import logging
import queue
from threading import RLock

from sawtooth_validator.concurrent.thread import InstrumentedThread
from sawtooth_validator.concurrent.threadpool import \
    InstrumentedThreadPoolExecutor
from sawtooth_validator.journal.block_wrapper import BlockStatus
from sawtooth_validator.journal.block_wrapper import BlockWrapper
from sawtooth_validator.journal.block_wrapper import NULL_BLOCK_IDENTIFIER
from sawtooth_validator.journal.consensus.consensus_factory import \
    ConsensusFactory
from sawtooth_validator.journal.chain_commit_state import ChainCommitState
from sawtooth_validator.journal.validation_rule_enforcer import \
    ValidationRuleEnforcer
from sawtooth_validator.state.settings_view import SettingsViewFactory
from sawtooth_validator.protobuf.transaction_pb2 import TransactionHeader
from sawtooth_validator.protobuf.transaction_receipt_pb2 import \
    TransactionReceipt
from sawtooth_validator.metrics.wrappers import CounterWrapper
from sawtooth_validator.metrics.wrappers import GaugeWrapper

from sawtooth_validator.state.merkle import INIT_ROOT_KEY
from sawtooth_validator.protobuf.block_pb2 import Block
from sawtooth_validator.consensus.proxy import UnknownBlock,TooManyBranch

LOGGER = logging.getLogger(__name__)

MAX_DAG_BRANCH = 3 # for DAG 

class BlockValidationAborted(Exception):
    """
    Indication that the validation of this fork has terminated for an
    expected(handled) case and that the processing should exit.
    """
    pass


class ChainHeadUpdated(Exception):
    """ Raised when a chain head changed event is detected and we need to abort
    processing and restart processing with the new chain head.
    """


class InvalidBatch(Exception):
    """ Raised when a batch fails validation as a signal to reject the
    block.
    """
    pass


# pylint: disable=stop-iteration-return
def look_ahead(iterable):
    """Pass through all values from the given iterable, augmented by the
    information if there are more values to come after the current one
    (True), or if it is the last value (False).
    """
    # Get an iterator and pull the first value.
    it = iter(iterable)
    last = next(it)
    # Run the iterator to exhaustion (starting from the second value).
    for val in it:
        # Report the *previous* value (more to come).
        yield last, True
        last = val
    # Report the last value.
    yield last, False


class BlockValidator(object):
    """
    Responsible for validating a block, handles both chain extensions and fork
    will determine if the new block should be the head of the chain and return
    the information necessary to do the switch if necessary.
    """

    def __init__(self,
                 consensus_module,
                 block_cache,
                 new_block,
                 state_view_factory,
                 done_cb,
                 executor,
                 recompute_context,
                 squash_handler,
                 context_handlers,
                 identity_signer,
                 data_dir,
                 config_dir,
                 permission_verifier,
                 metrics_registry=None,
                 block_manager=None):
        """Initialize the BlockValidator
        Args:
             consensus_module: The consensus module that contains
             implementation of the consensus algorithm to use for block
             validation.
             block_cache: The cache of all recent blocks and the processing
             state associated with them.
             new_block: The block to validate.
             state_view_factory: The factory object to create.
             done_cb: The method to call when block validation completed
             executor: The thread pool to process block validations.
             squash_handler: A parameter passed when creating transaction
             schedulers.
             identity_signer: A cryptographic signer for signing blocks.
             data_dir: Path to location where persistent data for the
             consensus module can be stored.
             config_dir: Path to location where config data for the
             consensus module can be found.
        Returns:
            None
        """
        self._consensus_module = consensus_module
        self._block_manager = block_manager
        self._verifier = None      # for proxy only
        self._fork_resolver = None # for proxy only
        self._block_cache = block_cache
        self._chain_commit_state = ChainCommitState(
            self._block_cache.block_store, [])
        self._new_block = new_block
        
        # Set during execution of the of the  BlockValidation to the current
        # chain_head at that time.
        self._chain_head = None

        self._state_view_factory = state_view_factory
        self._done_cb = done_cb
        self._executor = executor
        self._recompute_context = recompute_context
        self._squash_handler = squash_handler
        self._context_handlers = context_handlers 
        self._check_merkle = context_handlers['check_merkle']
        self._get_merkle_root = context_handlers['merkle_root']
        self._identity_signer = identity_signer
        self._data_dir = data_dir
        self._config_dir = config_dir
        self._result = {
            'new_block': new_block,
            'chain_head': None ,  # start with this head
            'new_chain': [],
            'cur_chain': [],
            'committed_batches': [],
            'uncommitted_batches': [],
            'num_transactions': 0
        }
        LOGGER.debug('BlockValidator: init _recompute_context=%s new_block=%s',self._recompute_context,type(new_block))
        self._permission_verifier = permission_verifier

        self._validation_rule_enforcer = \
            ValidationRuleEnforcer(SettingsViewFactory(state_view_factory))

        if metrics_registry:
            self._moved_to_fork_count = CounterWrapper(
                metrics_registry.counter('chain_head_moved_to_fork_count'))
        else:
            self._moved_to_fork_count = CounterWrapper()

    def _get_previous_block_root_state_hash(self, blkw):
        if blkw.previous_block_id == NULL_BLOCK_IDENTIFIER:
            return INIT_ROOT_KEY
        """
        for DAG use last root state fixed in the merkle
        because self._block_cache[blkw.previous_block_id].state_root_hash could be not correct 
        because of concurrence block with max number could has not last merkle root, so take root from merkle directly
        """
        main_head = self._block_cache.block_store.chain_head
        state_root_hash = self._get_merkle_root()
        LOGGER.debug('BlockValidator: get block root state for BLOCK=%s STATE=%s:%s REAL=%s\n',blkw.identifier[:8],main_head.block_num,main_head.state_root_hash[:10],state_root_hash[:10])
        return state_root_hash #main_head.state_root_hash
        #return self._block_cache[blkw.previous_block_id].state_root_hash

    def _txn_header(self, txn):
        txn_hdr = TransactionHeader()
        txn_hdr.ParseFromString(txn.header)
        return txn_hdr

    def _verify_batch_transactions(self, batch):
        """Verify that all transactions in are unique and that all
        transactions dependencies in this batch have been satisfied, ie
        already committed by this block or prior block in the chain.

        :param batch: the batch to verify
        :return:
        Boolean: True if all dependencies are present and all transactions
        are unique.
        """
        for txn in batch.transactions:
            txn_hdr = self._txn_header(txn)
            if self._chain_commit_state.has_transaction(txn.header_signature):
                LOGGER.debug("Block rejected due to duplicate transaction, transaction: %s",txn.header_signature[:8])
                raise InvalidBatch()
            for dep in txn_hdr.dependencies:
                if not self._chain_commit_state.has_transaction(dep):
                    LOGGER.debug("Block rejected due to missing transaction dependency, transaction %s depends on %s",txn.header_signature[:8],dep[:8])
                    raise InvalidBatch()
            self._chain_commit_state.add_txn(txn.header_signature)

    def _verify_block_batches(self, blkw):
        if blkw.block.batches:
            """
            check again using proc of transactions
            FOR DAG prev_state could be different from merkle state which was used into publisher FIXME 
            """
            prev_state = self._get_previous_block_root_state_hash(blkw)
            # Use root state from previous block for DAG use last state
            # 
            LOGGER.debug("Have processed transactions again for block %s STATE=%s",blkw.identifier[:8],prev_state[:10])
            scheduler = self._executor.create_scheduler(self._squash_handler,prev_state,self._context_handlers)
            recomputed_state = scheduler.recompute_merkle_root(prev_state,self._recompute_context)
            
            if recomputed_state != blkw.state_root_hash:
                LOGGER.debug("recomputed STATE=%s is not match with state hash from block",recomputed_state[:10])
                scheduler.update_state_hash(blkw.state_root_hash,recomputed_state)

            self._executor.execute(scheduler)
            
            # testing
            #self._check_merkle(blkw.state_root_hash,'NEW before execution')

            try:
                for batch, has_more in look_ahead(blkw.block.batches):
                    if self._chain_commit_state.has_batch(batch.header_signature):
                        LOGGER.debug("Block(%s) rejected due to duplicate batch, batch: %s", blkw,batch.header_signature[:8])
                        raise InvalidBatch()

                    self._verify_batch_transactions(batch)
                    self._chain_commit_state.add_batch(
                        batch, add_transactions=False)
                    if has_more:
                        scheduler.add_batch(batch)
                    else:
                        # blkw.state_root_hash - new state calculated into publisher - for DAG it could be incorrect 
                        # we should recalculate it  
                        #LOGGER.debug("VERIFY BLOCK BATCHES: add batch for block=%s  STATE=%s-->%s",blkw.identifier[:8],prev_state[:10],blkw.state_root_hash[:10])
                        scheduler.add_batch(batch,recomputed_state if blkw.state_root_hash != recomputed_state else blkw.state_root_hash) # prev_state
            except InvalidBatch:
                LOGGER.debug("Invalid batch %s encountered during verification of block %s",batch.header_signature[:8],blkw)
                scheduler.cancel()
                return False
            except Exception:
                scheduler.cancel()
                raise

            scheduler.finalize()
            scheduler.complete(block=True)
            state_hash = None
            #
            # at this point new block state appeared into state database
            # testing
            #self._check_merkle(prev_state,'_verify_block_batches OLD root')
            #self._check_merkle(recomputed_state,'_verify_block_batches NEW root') #blkw.state_root_hash

            for batch in blkw.batches:
                batch_result = scheduler.get_batch_execution_result(batch.header_signature)
                if batch_result is not None and batch_result.is_valid:
                    txn_results = scheduler.get_transaction_execution_results(batch.header_signature)
                    blkw.execution_results.extend(txn_results)
                    state_hash = batch_result.state_hash
                    blkw.num_transactions += len(batch.transactions)
                    #LOGGER.debug("Block=%s NEW ROOT STATE=%s",blkw.identifier[:8],state_hash[:10])
                else:
                    return False
            if recomputed_state != state_hash: # blkw.state_root_hash != state_hash
                # for DAG this states could be different
                LOGGER.debug("Block(%s) rejected due to state root hash mismatch: %s != %s(FOR DAG TRY IGNORE)\n", blkw, blkw.state_root_hash[:10],state_hash[:10])
                return False

        return True

    def _validate_permissions(self, blkw):
        """
        Validate that all of the batch signers and transaction signer for the
        batches in the block are permitted by the transactor permissioning
        roles stored in state as of the previous block. If a transactor is
        found to not be permitted, the block is invalid.
        """
        if blkw.block_num != 0:
            try:
                state_root = self._get_previous_block_root_state_hash(blkw)
            except KeyError:
                LOGGER.info("Block rejected due to missing predecessor: %s", blkw)
                return False

            for batch in blkw.batches:
                if not self._permission_verifier.is_batch_signer_authorized(
                        batch, state_root):
                    return False
        return True

    def _validate_on_chain_rules(self, blkw):
        """
        Validate that the block conforms to all validation rules stored in
        state. If the block breaks any of the stored rules, the block is
        invalid.
        """
        if blkw.block_num != 0:
            try:
                state_root = self._get_previous_block_root_state_hash(blkw)
            except KeyError:
                LOGGER.debug("Block rejected due to missing" + " predecessor: %s", blkw)
                return False

            return self._validation_rule_enforcer.validate(blkw, state_root)
        return True

    def on_check_block(self):
        # for external consensus
        LOGGER.debug('BlockValidator: on_check_block say validator about reply\n')
        self._verifier.verify_block_complete(True)

    def on_commit_block(self):
        # for external consensus
        LOGGER.debug('BlockValidator: on_commit_block say validator about reply\n')
        self._fork_resolver.compare_forks_complete(True)

    def on_ignore_block(self):
        # for external consensus
        LOGGER.debug('BlockValidator: on_ignore_block say validator about reply\n')
        self._fork_resolver.compare_forks_complete(False)

    def on_fail_block(self):
        # for external consensus
        LOGGER.debug('BlockValidator: on_fail_block say validator about reply\n')
        self._verifier.verify_block_complete(False)
    def validate_block(self, blkw):
        # pylint: disable=broad-except
        LOGGER.debug("BlockValidator:validate_block...")
        try:
            if blkw.status == BlockStatus.Valid:
                return True
            elif blkw.status == BlockStatus.Invalid:
                return False
            else:
                valid = True
                LOGGER.debug("BlockValidator:validate_block -> _validate_permissions")
                valid = self._validate_permissions(blkw)

                if valid:
                    public_key = \
                        self._identity_signer.get_public_key().as_hex()
                    verifier = self._consensus_module.BlockVerifier(
                        block_cache=self._block_cache,
                        state_view_factory=self._state_view_factory,
                        data_dir=self._data_dir,
                        config_dir=self._config_dir,
                        validator_id=public_key)
                    self._verifier = verifier # save for reply from external consensus

                    LOGGER.debug("BlockValidator:validate_block -> verify_block")
                    """
                    use proxy engine for verification and send message NEW_BLOCK to consensus
                    when we got return from verifier.verify_block() consensus already say OK or BAD for this block     
                    """
                    valid = verifier.verify_block(blkw)
                    LOGGER.debug("BlockValidator:validate_block <- verify_block=%s",valid)
                    
                if valid:
                    valid = self._validate_on_chain_rules(blkw)

                if valid:
                    valid = self._verify_block_batches(blkw)

                # since changes to the chain-head can change the state of the
                # blocks in BlockStore we have to revalidate this block.
                block_store = self._block_cache.block_store
                #FIXME for DAG - think about block_store.chain_head 
                if (self._chain_head is not None
                        and self._chain_head.identifier != block_store.chain_head.identifier
                        and self._chain_head.identifier not in block_store.chain_heads):
                    LOGGER.debug("BlockValidator:validate_block raise ChainHeadUpdated")
                    raise ChainHeadUpdated()

                blkw.status = BlockStatus.Valid if valid else BlockStatus.Invalid
                if not valid and hasattr(verifier, 'verify_block_invalid'):
                    verifier.verify_block_invalid(blkw)

                LOGGER.debug("BlockValidator:validate_block valid=%s",valid)

                return valid
        except ChainHeadUpdated as chu:
            raise chu
        except Exception:
            LOGGER.exception("Unhandled exception BlockPublisher.validate_block()")
            return False

    def _find_common_height(self, new_chain, cur_chain):
        """
        Walk back on the longest chain until we find a predecessor that is the
        same height as the other chain.
        The blocks are recorded in the corresponding lists
        and the blocks at the same height are returned
        FIXME for DAG version
        """
        new_blkw = self._new_block
        cur_blkw = self._chain_head
        # 1) find the common ancestor of this block in the current chain
        # Walk back until we have both chains at the same length

        # Walk back the new chain to find the block that is the
        # same height as the current head.
        if new_blkw.block_num > cur_blkw.block_num:
            # new chain is longer
            # walk the current chain back until we find the block that is the
            # same height as the current chain.
            while new_blkw.block_num > cur_blkw.block_num and \
                    new_blkw.previous_block_id != NULL_BLOCK_IDENTIFIER:
                new_chain.append(new_blkw)
                try:
                    new_blkw = self._block_cache[new_blkw.previous_block_id]
                except KeyError:
                    LOGGER.info(
                        "Block %s rejected due to missing predecessor %s",
                        new_blkw,
                        new_blkw.previous_block_id)
                    for b in new_chain:
                        b.status = BlockStatus.Invalid
                    raise BlockValidationAborted()
        elif new_blkw.block_num < cur_blkw.block_num:
            # current chain is longer
            # walk the current chain back until we find the block that is the
            # same height as the new chain.
            while (cur_blkw.block_num > new_blkw.block_num
                   and new_blkw.previous_block_id != NULL_BLOCK_IDENTIFIER):
                cur_chain.append(cur_blkw)
                cur_blkw = self._block_cache[cur_blkw.previous_block_id]
        return (new_blkw, cur_blkw)

    def _find_common_ancestor(self, new_blkw, cur_blkw, new_chain, cur_chain):
        """ Finds a common ancestor of the two chains.
            FIXME for DAG version
        """
        while cur_blkw.identifier != new_blkw.identifier:
            if (cur_blkw.previous_block_id == NULL_BLOCK_IDENTIFIER
                    or new_blkw.previous_block_id == NULL_BLOCK_IDENTIFIER):
                # We are at a genesis block and the blocks are not the same
                LOGGER.info("Block rejected due to wrong genesis: %s %s",cur_blkw, new_blkw)
                for b in new_chain:
                    b.status = BlockStatus.Invalid
                raise BlockValidationAborted()
            new_chain.append(new_blkw)
            try:
                new_blkw = self._block_cache[new_blkw.previous_block_id]
            except KeyError:
                LOGGER.info(
                    "Block %s rejected due to missing predecessor %s",
                    new_blkw,
                    new_blkw.previous_block_id)
                for b in new_chain:
                    b.status = BlockStatus.Invalid
                raise BlockValidationAborted()

            cur_chain.append(cur_blkw)
            cur_blkw = self._block_cache[cur_blkw.previous_block_id]

    def _test_commit_new_chain(self):
        """ Compare the two chains and determine which should be the head.
        """
        public_key = self._identity_signer.get_public_key().as_hex()
        fork_resolver = \
            self._consensus_module.ForkResolver(
                block_cache=self._block_cache,
                state_view_factory=self._state_view_factory,
                data_dir=self._data_dir,
                config_dir=self._config_dir,
                validator_id=public_key)
        self._fork_resolver = fork_resolver # for proxy
        return fork_resolver.compare_forks(self._chain_head, self._new_block)

    def _compute_batch_change(self, new_chain, cur_chain):
        """
        Compute the batch change sets.
        """
        committed_batches = []
        for blkw in new_chain:
            for batch in blkw.batches:
                committed_batches.append(batch)

        uncommitted_batches = []
        for blkw in cur_chain:
            for batch in blkw.batches:
                uncommitted_batches.append(batch)

        return (committed_batches, uncommitted_batches)

    def run(self):
        """
        Main entry for Block Validation, Take a given candidate block
        and decide if it is valid then if it is valid determine if it should
        be the new head block. Returns the results to the ChainController
        so that the change over can be made if necessary.
        """
        try:
            branch_id = self._new_block.previous_block_id
            LOGGER.info("BlockValidator:run Starting validation NEW BLOCK=%s for BRANCH=%s",self._new_block.identifier[:8],branch_id[:8])
            cur_chain = self._result["cur_chain"]  # ordered list of the
            # current chain blocks
            new_chain = self._result["new_chain"]  # ordered list of the new chain blocks
            """
            FIXME get the current chain_head .For DAG we should take head for branch relating to _new_block
            """
            self._chain_head = self._block_cache.block_store.chain_head
            if self._chain_head.identifier != branch_id:
                # this is DAG version 
                self._chain_head = self._block_cache.block_store.get_chain_head(branch_id) 
                LOGGER.info("BlockValidator:run get head for BRANCH=%s num=%s",self._chain_head.identifier[:8],self._chain_head.block_num)
            self._result['chain_head'] = self._chain_head
            
            LOGGER.info("BlockValidator:: try to add new block chain_head=%s~%s head num=%s", self._chain_head.identifier[:8],branch_id[:8],self._chain_head.block_num)
            # 1) Find the common ancestor block, the root of the fork.
            # walk back till both chains are the same height
            (new_blkw, cur_blkw) = self._find_common_height(new_chain,cur_chain)

            # 2) Walk back until we find the common ancestor
            self._find_common_ancestor(new_blkw, cur_blkw,new_chain, cur_chain)

            # 3) Determine the validity of the new fork
            # build the transaction cache to simulate the state of the
            # chain at the common root.
            self._chain_commit_state = ChainCommitState(self._block_cache.block_store, cur_chain)

            valid = True
            for block in reversed(new_chain):
                if valid:
                    if not self.validate_block(block):
                        LOGGER.info("Block validation failed: %s", block)
                        valid = False
                    self._result["num_transactions"] += block.num_transactions
                else:
                    LOGGER.info("Block marked invalid (invalid predecessor): %s",block)
                    block.status = BlockStatus.Invalid

            if not valid:
                self._done_cb(False, self._result)
                return

            LOGGER.info("Block is Valid new_chain=%s cur_chain=%s",len(new_chain),len(cur_chain))
            # 4) Evaluate the 2 chains to see if the new chain should be
            # committed
            LOGGER.info("Comparing current chain head '%s' against new block '%s'",self._chain_head, self._new_block)
            for i in range(max(len(new_chain), len(cur_chain))):
                cur = new = num = "-"
                if i < len(cur_chain):
                    cur = cur_chain[i].header_signature[:8]
                    num = cur_chain[i].block_num
                if i < len(new_chain):
                    new = new_chain[i].header_signature[:8]
                    num = new_chain[i].block_num
                LOGGER.info("Fork comparison at height %s is between %s and %s",num, cur, new)
            # testing
            #self._check_merkle(self._new_block.state_root_hash,'_test_commit_new_chain')

            # fork_resolver - for proxy send message  
            commit_new_chain = self._test_commit_new_chain()

            # 5) Consensus to compute batch sets (only if we are switching).
            if commit_new_chain:
                (self._result["committed_batches"],
                 self._result["uncommitted_batches"]) = \
                    self._compute_batch_change(new_chain, cur_chain)

                if new_chain[0].previous_block_id != \
                        self._chain_head.identifier:
                    self._moved_to_fork_count.inc()

            # 6) Tell the journal we are done.
            LOGGER.info("_done_cb  commit_new_chain=%s\n",commit_new_chain)
            #self._check_merkle(self._new_block.state_root_hash)
            self._done_cb(commit_new_chain, self._result)

            LOGGER.info("Finished new block=%s validation STATE=%s\n",self._new_block.block_num,self._new_block.state_root_hash)
            self._check_merkle(self._new_block.state_root_hash)
            

        except BlockValidationAborted:
            self._done_cb(False, self._result)
            return
        except ChainHeadUpdated:
            self._done_cb(False, self._result)
            return
        except Exception:  # pylint: disable=broad-except
            LOGGER.exception(
                "Block validation failed with unexpected error: %s",
                self._new_block)
            # callback to clean up the block out of the processing list.
            self._done_cb(False, self._result)


class ChainObserver(object, metaclass=ABCMeta):
    @abstractmethod
    def chain_update(self, block, receipts):
        """This method is called by the ChainController on block boundaries.

        Args:
            block (:obj:`BlockWrapper`): The block that was just committed.
            receipts (dict of {str: receipt}): Map of transaction signatures to
                transaction receipts for all transactions in the block."""
        raise NotImplementedError()


class _ChainThread(InstrumentedThread):
    def __init__(self, chain_controller, block_queue, block_cache):
        super().__init__(name='_ChainThread')
        self._chain_controller = chain_controller
        self._block_queue = block_queue
        self._block_cache = block_cache
        self._exit = False

    def run(self):
        try:
            while True:
                try:
                    block = self._block_queue.get(timeout=1)
                    LOGGER.debug("_ChainThread NEW BLOCK: %s",block)
                    self._chain_controller.on_block_received(block)
                except queue.Empty:
                    # If getting a block times out, just try again.
                    pass

                if self._exit:
                    return
        # pylint: disable=broad-except
        except Exception:
            LOGGER.exception("ChainController thread exited with error.")

    def stop(self):
        self._exit = True


class ChainController(object):
    """
    To evaluating new blocks to determine if they should extend or replace
    the current chain. If they are valid extend the chain.
    """

    def __init__(self,
                 block_cache,
                 block_sender,
                 state_view_factory,
                 transaction_executor,
                 chain_head_lock,
                 on_chain_updated,
                 on_head_updated,
                 get_recompute_context,
                 squash_handler,
                 context_handlers,
                 chain_id_manager,
                 identity_signer,
                 data_dir,
                 config_dir,
                 permission_verifier,
                 chain_observers,
                 thread_pool=None,
                 metrics_registry=None,
                 consensus_notifier=None,
                 block_manager=None,
                 max_dag_branch=None):
        """Initialize the ChainController
        Args:
            block_cache: The cache of all recent blocks and the processing
                state associated with them.
            block_sender: an interface object used to send blocks to the
                network.
            state_view_factory: The factory object to create
            transaction_executor: The TransactionExecutor used to produce
                schedulers for batch validation.
            chain_head_lock: Lock to hold while the chain head is being
                updated, this prevents other components that depend on the
                chain head and the BlockStore from having the BlockStore change
                under them. This lock is only for core Journal components
                (BlockPublisher and ChainController), other components should
                handle block not found errors from the BlockStore explicitly.
            block_publisher.on_chain_updated: The callback to call to notify the rest of the
                 system the head block in the chain has been changed.
                 squash_handler: a parameter passed when creating transaction
                 schedulers.
            chain_id_manager: The ChainIdManager instance.
            identity_signer: Private key for signing blocks.
            data_dir: path to location where persistent data for the
                consensus module can be stored.
            config_dir: path to location where config data for the
                consensus module can be found.
            chain_observers (list of :obj:`ChainObserver`): A list of chain
                observers.
        Returns:
            None
        """
        self._lock = RLock()
        self._chain_head_lock = chain_head_lock
        self._block_cache = block_cache
        self._block_store = block_cache.block_store
        self._state_view_factory = state_view_factory
        self._block_sender = block_sender
        self._transaction_executor = transaction_executor
        self._notify_on_chain_updated = on_chain_updated
        self._notify_on_head_updated = on_head_updated
        self._get_recompute_context = get_recompute_context
        self._squash_handler = squash_handler
        self._context_handlers=context_handlers
        self._identity_signer = identity_signer
        self._data_dir = data_dir
        self._config_dir = config_dir

        self._blocks_processing = {}  # a set of blocks that are
        # currently being processed.
        self._blocks_pending = {}  # set of blocks that the previous block
        # is being processed. Once that completes this block will be
        # scheduled for validation.
        self._chain_id_manager = chain_id_manager

        self._chain_head = None # main branch
        self._chain_heads = {} # for DAG only
        self._permission_verifier = permission_verifier
        self._chain_observers = chain_observers
        self._metrics_registry = metrics_registry
        self._consensus_notifier = consensus_notifier # for external consensus
        self._block_manager = block_manager
        self._max_dag_branch = max_dag_branch if max_dag_branch is not None else MAX_DAG_BRANCH
        LOGGER.info("Chain controller initialized with max_dag_branch=%s",self._max_dag_branch)
        if metrics_registry:
            self._chain_head_gauge = GaugeWrapper(
                metrics_registry.gauge('chain_head', default='no chain head'))
            self._committed_transactions_count = CounterWrapper(
                metrics_registry.counter('committed_transactions_count'))
            self._block_num_gauge = GaugeWrapper(
                metrics_registry.gauge('block_num'))
            self._blocks_considered_count = CounterWrapper(
                metrics_registry.counter('blocks_considered_count'))
        else:
            self._chain_head_gauge = GaugeWrapper()
            self._committed_transactions_count = CounterWrapper()
            self._block_num_gauge = GaugeWrapper()
            self._blocks_considered_count = CounterWrapper()

        self._block_queue = queue.Queue()
        self._thread_pool = (
            InstrumentedThreadPoolExecutor(max_workers=self._max_dag_branch, name='Validating')
            if thread_pool is None else thread_pool
        )
        self._chain_thread = None

        # Only run this after all member variables have been bound
        self._set_chain_head_from_block_store()

    def _set_chain_head_from_block_store(self):
        try:
            # main chain head
            self._chain_head = self._block_store.chain_head
            if self._chain_head is not None:
                LOGGER.info("Chain controller initialized with main chain head: %s",self._chain_head)
                hid = self._chain_head.identifier
                # add main BRANCH for DAG chain
                self._chain_heads[hid] = self._chain_head
                self._block_store.update_chain_heads(hid,self._chain_head)
                self._chain_head_gauge.set_value(hid[:8])
        except Exception:
            LOGGER.exception("Invalid block store. Head of the block chain cannot be determined")
            raise

    def start(self):
        self._set_chain_head_from_block_store()
        LOGGER.debug("ChainController:START call _notify PUBLISHER on_chain_updated ID=%s\n",self._chain_head.identifier[:8])
        self._notify_on_chain_updated(self._chain_head)

        self._chain_thread = _ChainThread(
            chain_controller=self,
            block_queue=self._block_queue,
            block_cache=self._block_cache)
        self._chain_thread.start()

    def stop(self):
        if self._chain_thread is not None:
            self._chain_thread.stop()
            self._chain_thread = None

        if self._thread_pool is not None:
            self._thread_pool.shutdown(wait=True)

    def queue_block(self, block):
        """
        New block has been received, queue it with the chain controller
        for processing.
        from publisher.on_check_publish_block() 
        """
        LOGGER.debug("ChainController: queue BLOCK=%s",block.identifier[:8])
        self._block_queue.put(block)

    def get_chain_head(self,parent_id=None,new_parent_id=None):
        """
        for DAG version - in case new_parent_id != None - switch parent_id to new_parent_id block as new branch 
        """ 
        if parent_id is None:
            return self._chain_head
        if parent_id in self._chain_heads:
            if new_parent_id is not None and new_parent_id in self._block_cache:
                # switch 'parent_id' head to new point 
                LOGGER.debug("ChainController: switch BRANCH %s->%s heads=%s",parent_id[:8],new_parent_id[:8],[str(blk.block_num)+':'+key[:8] for key,blk in self._chain_heads.items()])
                new_head = self._block_cache[new_parent_id]
                del self._chain_heads[parent_id]
                self._chain_heads[new_parent_id] = new_head
                self._block_store.update_branch(parent_id,new_parent_id,new_head)
                self._notify_on_head_updated(parent_id,new_parent_id,new_head)
                LOGGER.debug("ChainController: swithed BRANCH %s",[str(blk.block_num)+':'+key[:8] for key,blk in self._chain_heads.items()])
                return new_head

            return self._chain_heads[parent_id]
        else:
            LOGGER.debug("ChainController: get_chain_head BRANCHES=%s",[key[:8] for key in self._chain_heads.keys()])

        if len(self._chain_heads) >= self._max_dag_branch :
            LOGGER.debug("ChainController: TOO MANY NEW BRANCH %s ",[str(blk.block_num)+':'+key[:8] for key,blk in self._chain_heads.items()])
            raise TooManyBranch
            #return None
        # create new branch for DAG
        if parent_id in self._block_cache:
            # mark block into block_store as new DAG branch 
            LOGGER.debug("ChainController: get_chain_head NEW BRANCH=%s",parent_id[:8])
            new_head = self._block_cache[parent_id]
            self._block_store.add_branch(parent_id,new_head)
            self._chain_heads[parent_id] = new_head
            return new_head
        return None

    @property
    def chain_head(self):
        # FIXME - investigate what we should return for DAG here
        return self._chain_head

    def _submit_blocks_for_verification(self, blocks):
        for blkw in blocks:
            branch_id = blkw.previous_block_id
            LOGGER.debug("_submit_blocks_for_verification BRANCH=%s chain heads=%s",branch_id[:8],[str(blk.block_num)+':'+key[:8] for key,blk in self._chain_heads.items()])
            chain_head = self._chain_heads[branch_id]
            main_head = main_head = self._block_cache.block_store.chain_head
            state_view = BlockWrapper.state_view_for_block(main_head,self._state_view_factory) # for DAG use main_head instead chain_head
            LOGGER.debug("ChainController: _submit_blocks_for_verification BRANCH=%s head=%s",branch_id[:8],chain_head == self.chain_head)
            """
            consensus_module = \
                ConsensusFactory.get_configured_consensus_module(
                    self.chain_head.header_signature,
                    state_view)
            """
            consensus_module,consensus_name = ConsensusFactory.try_configured_consensus_module(chain_head.header_signature,state_view)
            
            if not consensus_module:
                # there is no internal consensus 
                # check may consensus engine already was registred
                LOGGER.debug("ChainController: no internal consensus_module=%s use proxy",consensus_name)
                #self._consensus = consensus_name[0] # save consensus name
                consensus_module = ConsensusFactory.try_configured_proxy_consensus()
                consensus_module._CONSENSUS_NAME_ = consensus_name[0]
                consensus_module._consensus_notifier = self._consensus_notifier
                if self._block_manager:
                    # add NEW block into block manager 
                    blk = blkw.get_block()
                    self._block_manager.put([blk])
                    self._block_manager.ref_block(blk.header_signature)
                    """
                    mark parent block ref_block(blk.previous_block_id) 
                    """
                    self._block_manager.ref_block(blkw.header.previous_block_id)
                    #block_iter = self._block_manager.get([blk.header_signature])
                    #blocks = [b for b in block_iter]
                    #blocks = next(self._block_manager.get([blk.header_signature]))
                    #LOGGER.debug("BlockValidator:validate_block blocks=%s",blocks)

            validator = BlockValidator(
                consensus_module=consensus_module,
                new_block=blkw,
                block_cache=self._block_cache,
                state_view_factory=self._state_view_factory,
                done_cb=self.on_block_validated,
                executor=self._transaction_executor,
                recompute_context=self._get_recompute_context(branch_id),
                squash_handler=self._squash_handler,
                context_handlers=self._context_handlers,
                identity_signer=self._identity_signer,
                data_dir=self._data_dir,
                config_dir=self._config_dir,
                permission_verifier=self._permission_verifier,
                metrics_registry=self._metrics_registry,
                block_manager=self._block_manager)
            self._blocks_processing[blkw.block.header_signature] = validator
            self._thread_pool.submit(validator.run)
            LOGGER.debug("ChainController:_submit_blocks_for_verification DONE block=%s",blkw.block.header_signature[:8])

    """
    for external consensus
    """ 
    def get_block_from_cache(self,block_id):
        return self._block_cache[block_id]

    def on_check_block(self,block_id):
        # for external consensus - say that verification was done
        bid = block_id.hex()
        LOGGER.debug('ChainController: on_check_block block=%s num=%s\n',bid[:8],len(self._blocks_processing))
        
        if bid in self._blocks_processing : 
            validator = self._blocks_processing[bid]
            validator.on_check_block()
            
        else:
            LOGGER.debug('ChainController: on_check_block NO block=%s blocks_processing=%s',bid,self._blocks_processing)

    def block_validation_result(self, block_id):
        # for external consensus
        """
        status = ctypes.c_int32(0)

        _libexec("chain_controller_block_validation_result", self.pointer,
                 ctypes.c_char_p(block_id.encode()),
                 ctypes.byref(status))
        """
        if block_id in self._blocks_processing : 
            validator = self._blocks_processing[block_id]
            LOGGER.debug("ChainController:block_validation_result validator=%s",validator._new_block.status)
            return validator._new_block.status #BlockStatus.Valid
        else:
            LOGGER.debug("ChainController:block_validation_result id=%s blocks_processing=%s",block_id.hex(),self._blocks_processing)
            return BlockStatus.Unknown #BlockStatus(status.value)

    def get_blocks_validation(self, block_ids):
        # for external consensus
        blocks = []
        for block_id in block_ids:
            if block_id in self._blocks_processing : 
                validator = self._blocks_processing[block_id]
                LOGGER.debug("ChainController:block_validation_result validator=%s",validator._new_block.status)
                blocks.append(validator._new_block)
        return blocks

    def commit_block(self, block):   
        # for external consensus     
        block_id = block.hex()
        if block_id in self._blocks_processing :
            validator = self._blocks_processing[block_id]
            validator.on_commit_block()
        else:
            LOGGER.debug("ChainController:commit_block undefined id=%s",block_id)
            raise UnknownBlock

    def ignore_block(self, block):   
        # for external consensus     
        block_id = block.hex()
        if block_id in self._blocks_processing :
            validator = self._blocks_processing[block_id]
            validator.on_ignore_block()
        else:
            LOGGER.debug("ChainController:ignore_block undefined id=%s",block_id)
            raise UnknownBlock

    def fail_block(self,block):
        # for external consensus     
        block_id = block.hex()
        if block_id in self._blocks_processing :
            validator = self._blocks_processing[block_id]
            validator.on_fail_block()
        else:
            LOGGER.debug("ChainController:fail_block undefined id=%s",block_id)
            raise UnknownBlock

    def on_block_validated(self, commit_new_block, result):
        """
        call as done_cb() 
        Message back from the block validator, that the validation is
        complete
        Args:
        commit_new_block (Boolean): whether the new block should become the
        chain head or not.
        result (Dict): Map of the results of the fork resolution.
        Returns:
            None
        """
        try:
            with self._lock:
                self._blocks_considered_count.inc()
                new_block = result["new_block"]

                # remove from the processing list
                del self._blocks_processing[new_block.identifier]

                # Remove this block from the pending queue, obtaining any
                # immediate descendants of this block in the process.
                descendant_blocks = \
                    self._blocks_pending.pop(new_block.identifier, [])

                # if the head has changed, since we started the work.
                # FIXME for DAG check branch relating to new block 
                # result["chain_head"] is value from BlockValidator  for DAG we should analize here corresponding BRANCH 
                if result["chain_head"].identifier not in self._chain_heads: # OLD result["chain_head"].identifier != self._chain_head.identifier
                    LOGGER.info('Chain head updated from %s to %s while processing block: %s',
                        result["chain_head"],
                        self._chain_head,
                        new_block)

                    # If any immediate descendant blocks arrived while this
                    # block was being processed, then submit them for
                    # verification.  Otherwise, add this block back to the
                    # pending queue and resubmit it for verification.
                    if descendant_blocks:
                        LOGGER.debug('Verify descendant blocks: %s (%s)',new_block,[block.identifier[:8] for block in descendant_blocks])
                        self._submit_blocks_for_verification(descendant_blocks)

                    else:
                        LOGGER.debug('Verify block again: %s ', new_block)
                        self._blocks_pending[new_block.identifier] = []
                        self._submit_blocks_for_verification([new_block])

                # If the head is to be updated to the new block.
                elif commit_new_block:
                    bid = new_block.previous_block_id 
                    nid = new_block.identifier
                    LOGGER.debug("ChainController:on_block_validated COMMIT NEW BLOCK[%s]=%s for BRANCH=%s\n",new_block.block_num,nid[:8],bid[:8])
                    with self._chain_head_lock:
                        # FIXME - change head for branch==bid into self._chain_heads
                        #
                        # say that block number really used
                        self._block_store.pop_block_number(new_block.block_num)
                        if bid in self._chain_heads:
                            # update head for branch bid
                            del self._chain_heads[bid]
                            self._chain_heads[nid] = new_block
                            self._block_store.update_chain_heads(nid,new_block)
                            LOGGER.debug("ChainController:update head for BRANCH=%s->%s num=%s cur=%s",bid[:8],nid[:8],len(self._chain_heads),len(result["cur_chain"]))
                        # for DAG self._chain_head just last update branch's head it could be local variable 
                        self._chain_head = new_block

                        # update the the block store to have the new chain
                        self._block_store.update_chain(result["new_chain"],result["cur_chain"])

                        # make sure old chain is in the block_caches
                        self._block_cache.add_chain(result["cur_chain"])

                        LOGGER.info("Chain head branch=%s updated to: %s",bid[:8],self._chain_head)

                        self._chain_head_gauge.set_value(self._chain_head.identifier[:8])

                        self._committed_transactions_count.inc(result["num_transactions"])

                        self._block_num_gauge.set_value(self._chain_head.block_num)

                        LOGGER.debug("ChainController:_notify_on_chain_updated from on_block_validated ID=%s\n",self._chain_head.identifier[:8])
                        # tell the BlockPublisher else the chain for branch is updated
                        self._notify_on_chain_updated(
                            self._chain_head,
                            result["committed_batches"],
                            result["uncommitted_batches"])

                        for batch in new_block.batches:
                            if batch.trace:
                                LOGGER.debug("TRACE %s: %s",
                                             batch.header_signature,
                                             self.__class__.__name__)

                    # Submit any immediate descendant blocks for verification
                    LOGGER.debug(
                        'Verify descendant blocks: %s (%s)',
                        new_block,
                        [block.identifier[:8] for block in descendant_blocks])
                    self._submit_blocks_for_verification(descendant_blocks)

                    for block in reversed(result["new_chain"]):
                        receipts = self._make_receipts(block.execution_results)
                        # Update all chain observers
                        for observer in self._chain_observers:
                            observer.chain_update(block, receipts)

                # If the block was determine to be invalid.
                elif new_block.status == BlockStatus.Invalid:
                    # Since the block is invalid, we will never accept any
                    # blocks that are descendants of this block.  We are going
                    # to go through the pending blocks and remove all
                    # descendants we find and mark the corresponding block
                    # as invalid.
                    #
                    # Block could be invalid in case of consensus fail
                    # we should inform external consensus
                    LOGGER.debug("ChainController:on_block_validated BLOCK=%s INVALID\n",new_block.block_num)
                    self._block_store.free_block_number(new_block.block_num)
                    while descendant_blocks:
                        pending_block = descendant_blocks.pop()
                        pending_block.status = BlockStatus.Invalid

                        LOGGER.debug(
                            'Marking descendant block invalid: %s',
                            pending_block)

                        descendant_blocks.extend(
                            self._blocks_pending.pop(
                                pending_block.identifier,
                                []))

                # The block is otherwise valid, but we have determined we
                # don't want it as the chain head.
                else:
                    LOGGER.info('Rejected new chain head: %s', new_block)
                    self._block_store.free_block_number(new_block.block_num)
                    if self._consensus_notifier is not None:
                        # say external consensus 
                        self._consensus_notifier.notify_block_invalid(new_block.header_signature)
                    # Submit for verification any immediate descendant blocks
                    # that arrived while we were processing this block.
                    LOGGER.debug(
                        'Verify descendant blocks: %s (%s)',
                        new_block,
                        [block.identifier[:8] for block in descendant_blocks])
                    LOGGER.info('Rejected descendant_blocks num=%s',len(descendant_blocks))
                    self._submit_blocks_for_verification(descendant_blocks)

        # pylint: disable=broad-except
        except Exception:
            LOGGER.exception(
                "Unhandled exception in ChainController.on_block_validated()")

    def on_block_received(self, block):
        try:
            with self._lock:
                if self.has_block(block.header_signature):
                    # do we already have this block
                    return

                if self.chain_head is None:
                    self._set_genesis(block)
                    return

                # If we are already currently processing this block, then
                # don't bother trying to schedule it again.
                if block.identifier in self._blocks_processing:
                    return

                self._block_cache[block.identifier] = block
                self._blocks_pending[block.identifier] = []
                LOGGER.debug("Block received: id=%s", block.identifier[:8])
                if (block.previous_block_id in self._blocks_processing
                        or block.previous_block_id in self._blocks_pending):
                    LOGGER.debug('Block pending: id=%s', block.identifier[:8])
                    # if the previous block is being processed, put it in a
                    # wait queue, Also need to check if previous block is
                    # in the wait queue.
                    pending_blocks = self._blocks_pending.get(
                        block.previous_block_id,
                        [])
                    # Though rare, the block may already be in the
                    # pending_block list and should not be re-added.
                    if block not in pending_blocks:
                        pending_blocks.append(block)

                    self._blocks_pending[block.previous_block_id] = \
                        pending_blocks
                else:
                    # schedule this block for validation.
                    self._submit_blocks_for_verification([block])
        # pylint: disable=broad-except
        except Exception:
            LOGGER.exception(
                "Unhandled exception in ChainController.on_block_received()")

    def has_block(self, block_id):
        with self._lock:
            if block_id in self._block_cache:
                LOGGER.debug("ChainController: has_block in CACHE")
                return True

            if block_id in self._blocks_processing:
                LOGGER.debug("ChainController: has_block in PROCESSING")
                return True

            if block_id in self._blocks_pending:
                LOGGER.debug("ChainController: has_block in PENDING")
                return True

            return False


    def _set_genesis(self, block):
        # This is used by a non-genesis journal when it has received the
        # genesis block from the genesis validator
        if block.previous_block_id == NULL_BLOCK_IDENTIFIER:
            chain_id = self._chain_id_manager.get_block_chain_id()
            if chain_id is not None and chain_id != block.identifier:
                LOGGER.warning("Block id does not match block chain id %s. "
                               "Cannot set initial chain head.: %s",
                               chain_id[:8], block.identifier[:8])
            else:
                state_view = self._state_view_factory.create_view()
                LOGGER.debug("ChainController: _set_genesis")
                consensus_module = \
                    ConsensusFactory.get_configured_consensus_module(
                        NULL_BLOCK_IDENTIFIER,
                        state_view)

                if self._block_manager:
                    # add NEW blkw into block manager 
                    LOGGER.debug("ChainController: _set_genesis ADD NEW BLOCK\n")
                    blk = blkw.get_block()
                    self._block_manager.put([blk])
                    self._block_manager.ref_block(blk.header_signature)

                validator = BlockValidator(
                    consensus_module=consensus_module,
                    new_block=block,
                    block_cache=self._block_cache,
                    state_view_factory=self._state_view_factory,
                    done_cb=self.on_block_validated,
                    executor=self._transaction_executor,
                    squash_handler=self._squash_handler,
                    context_handlers=self._context_handlers, 
                    identity_signer=self._identity_signer,
                    data_dir=self._data_dir,
                    config_dir=self._config_dir,
                    permission_verifier=self._permission_verifier,
                    metrics_registry=self._metrics_registry,
                    block_manager=self._block_manager)

                valid = validator.validate_block(block)
                if valid:
                    if chain_id is None:
                        self._chain_id_manager.save_block_chain_id(block.identifier)

                    self._block_store.update_chain([block])
                    self._chain_head = block
                    LOGGER.debug("ChainController: _notify_on_chain_updated GENESIS ID=%s\n",self._chain_head.identifier[:8])
                    self._notify_on_chain_updated(self._chain_head)
                else:
                    LOGGER.warning("The genesis block is not valid. Cannot "
                                   "set chain head: %s", block)

        else:
            LOGGER.warning("Cannot set initial chain head, this is not a "
                           "genesis block: %s", block)

    def _make_receipts(self, results):
        receipts = []
        for result in results:
            receipt = TransactionReceipt()
            receipt.data.extend([data for data in result.data])
            receipt.state_changes.extend(result.state_changes)
            receipt.events.extend(result.events)
            receipt.transaction_id = result.signature
            receipts.append(receipt)
        return receipts
