# Copyright NTRLab NTR
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

# pylint: disable=inconsistent-return-statements

import abc
from collections import deque
import logging
import queue
from threading import RLock
import time

from sawtooth_validator.concurrent.thread import InstrumentedThread
from sawtooth_validator.execution.scheduler_exceptions import SchedulerError

from sawtooth_validator.journal.block_builder import BlockBuilder
from sawtooth_validator.journal.block_wrapper import BlockWrapper
from sawtooth_validator.journal.consensus.batch_publisher import \
    BatchPublisher
from sawtooth_validator.journal.consensus.consensus_factory import \
    ConsensusFactory

from sawtooth_validator.journal.chain_commit_state import \
    TransactionCommitCache

from sawtooth_validator.metrics.wrappers import CounterWrapper
from sawtooth_validator.metrics.wrappers import GaugeWrapper

from sawtooth_validator.protobuf.block_pb2 import BlockHeader
from sawtooth_validator.protobuf.transaction_pb2 import TransactionHeader

from sawtooth_validator.exceptions import NotRegisteredConsensusModule 
from sawtooth_sdk.consensus.exceptions import BlockNotReady 
LOGGER = logging.getLogger(__name__)


NUM_PUBLISH_COUNT_SAMPLES = 5
INITIAL_PUBLISH_COUNT = 30



class PendingBatchObserver(metaclass=abc.ABCMeta):
    """An interface class for components wishing to be notified when a Batch
    has begun being processed.
    """

    @abc.abstractmethod
    def notify_batch_pending(self, batch):
        """This method will be called when a Batch has passed initial
        validation and is queued to be processed by the Publisher.

        Args:
            batch (Batch): The Batch that has been added to the Publisher
        """
        raise NotImplementedError('PendingBatchObservers must have a '
                                  '"notify_batch_pending" method')


class _PublisherThread(InstrumentedThread):
    def __init__(self, block_publisher, batch_queue,
                 check_publish_block_frequency):
        super().__init__(name='_PublisherThread')
        self._block_publisher = block_publisher
        self._batch_queue = batch_queue
        self._check_publish_block_frequency = \
            check_publish_block_frequency
        self._exit = False

    def run(self):
        try:
            # make sure we don't check to publish the block
            # to frequently.
            next_check_publish_block_time = time.time() + \
                self._check_publish_block_frequency
            LOGGER.debug("_PublisherThread:run _check_publish_block_frequency=%s",self._check_publish_block_frequency)
            while True:
                try:
                    batch = self._batch_queue.get(
                        timeout=self._check_publish_block_frequency)
                    self._block_publisher.on_batch_received(batch)
                except queue.Empty:
                    # If getting a batch times out, just try again.
                    pass

                if next_check_publish_block_time < time.time():
                    self._block_publisher.on_check_publish_block()
                    next_check_publish_block_time = time.time() + \
                        self._check_publish_block_frequency
                if self._exit:
                    return
        # pylint: disable=broad-except
        except Exception as exc:
            LOGGER.exception(exc)
            LOGGER.critical("BlockPublisher thread exited with error.")

    def stop(self):
        self._exit = True


class _CandidateBlock(object):
    """This is a helper class for the BlockPublisher. The _CandidateBlock
    tracks all the state associated with the Block that is being built.
    This allows the BlockPublisher to focus on when to create and finalize
    a block and not worry about how the block is built.
    """

    def __init__(self,
                 block_store,
                 consensus,
                 scheduler,
                 committed_txn_cache,
                 block_builder,
                 max_batches,
                 batch_injectors,
                 identifier
                 ):
        self._pending_batches = []
        self._pending_batch_ids = set()
        self._injected_batch_ids = set()
        self._block_store = block_store
        self._consensus = consensus
        self._scheduler = scheduler
        self._committed_txn_cache = committed_txn_cache
        # Look-up cache for transactions that are committed in the current
        # chain and the state of the transactions already added to the
        # candidate block.
        self._block_builder = block_builder
        self._max_batches = max_batches
        self._batch_injectors = batch_injectors
        self._identifier = identifier

    def __del__(self):
        # Cancel the scheduler if it is not complete
        if not self._scheduler.complete(block=False):
            self._scheduler.cancel()

    @property
    def identifier(self):
        return self._identifier

    @property
    def block_num(self):
        return self._block_builder.block_num

    @property
    def previous_block_id(self):
        return self._block_builder.previous_block_id

    def has_pending_batches(self):
        return len(self._pending_batches) != 0

    @property
    def last_batch(self):
        if self._pending_batches:
            return self._pending_batches[-1]
        raise ValueError(
            'last_batch called on an empty block.'
            'Empty block publishing is not supported.'
        )

    @property
    def batches(self):
        return self._pending_batches.copy()

    @property
    def can_add_batch(self):
        return (
            self._max_batches == 0
            or len(self._pending_batches) < self._max_batches
        )

    def _check_batch_dependencies(self, batch, committed_txn_cache):
        """Check the dependencies for all transactions in this are present.
        If all are present the committed_txn is updated with all txn in this
        batch and True is returned. If they are not return failure and the
        committed_txn is not updated.
        :param batch: the batch to validate
        :param committed_txn_cache: The cache holding the set of committed
        transactions to check against, updated during processing.
        :return: Boolean, True if dependencies checkout, False otherwise.
        """
        for txn in batch.transactions:
            if self._is_txn_already_committed(txn, committed_txn_cache):
                LOGGER.debug(
                    "Transaction rejected as it is already in the chain %s",
                    txn.header_signature[:8])
                return False
            elif not self._check_transaction_dependencies(
                    txn, committed_txn_cache):
                # if any transaction in this batch fails the whole batch
                # fails.
                committed_txn_cache.remove_batch(batch)
                return False
            # update so any subsequent txn in the same batch can be dependent
            # on this transaction.
            committed_txn_cache.add(txn.header_signature)
        return True

    def _check_transaction_dependencies(self, txn, committed_txn_cache):
        """Check that all this transactions dependencies are present.
        :param txn: the transaction to check
        :param committed_txn_cache: The cache holding the set of committed
        transactions to check against.
        :return: Boolean, True if dependencies checkout, False otherwise.
        """
        txn_hdr = TransactionHeader()
        txn_hdr.ParseFromString(txn.header)
        for dep in txn_hdr.dependencies:
            if dep not in committed_txn_cache:
                LOGGER.debug(
                    "Transaction rejected due missing dependency, "
                    "transaction %s depends on %s",
                    txn.header_signature, dep)
                return False
        return True

    def _is_batch_already_committed(self, batch):
        """ Test if a batch is already committed to the chain or
        is already in the pending queue.
        :param batch: the batch to check
        """
        return (self._block_store.has_batch(batch.header_signature) or
                batch.header_signature in self._pending_batch_ids)

    def _is_txn_already_committed(self, txn, committed_txn_cache):
        """ Test if a transaction is already committed to the chain or
        is already in the pending queue.
        """
        return (self._block_store.has_batch(txn.header_signature) or
                txn.header_signature in committed_txn_cache)

    def _poll_injectors(self, poller, batch_list):
        for injector in self._batch_injectors:
            inject = poller(injector)
            if inject:
                for b in inject:
                    self._injected_batch_ids.add(b.header_signature)
                    batch_list.append(b)

    def add_batch(self, batch):
        """Add a batch to the _CandidateBlock
        :param batch: the batch to add to the block
        """
        if batch.trace:
            LOGGER.debug("TRACE %s: %s", batch.header_signature,
                         self.__class__.__name__)

        # first we check if the transaction dependencies are satisfied
        # The completer should have taken care of making sure all
        # Batches containing dependent transactions were sent to the
        # BlockPublisher prior to this Batch. So if there is a missing
        # dependency this is an error condition and the batch will be
        # dropped.
        if self._is_batch_already_committed(batch):
            # batch is already committed.
            LOGGER.debug("Dropping previously committed batch: %s",batch.header_signature)
            return
        elif self._check_batch_dependencies(batch, self._committed_txn_cache):
            batches_to_add = []

            # Inject batches at the beginning of the block
            if not self._pending_batches:
                self._poll_injectors(lambda injector: injector.block_start(
                    self._block_builder.previous_block_id), batches_to_add)

            batches_to_add.append(batch)
            LOGGER.debug("ADD_BATCH INTO BRANCH[%s]: len=%s batch=%s",self._identifier[:8],len(batches_to_add), batch.header_signature)
            for b in batches_to_add:
                self._pending_batches.append(b)
                self._pending_batch_ids.add(b.header_signature)
                try:
                    injected = b.header_signature in self._injected_batch_ids
                    LOGGER.debug("add_batch: add batch branch=%s",self._identifier[:8])
                    self._scheduler.add_batch(b, required=injected)
                except SchedulerError as err:
                    LOGGER.debug("Scheduler error processing batch: %s", err)
        else:
            LOGGER.debug("Dropping batch due to missing dependencies: %s",
                         batch.header_signature)

    def check_publish_block(self):
        """Check if it is okay to publish this candidate.
        """
        return self._consensus.check_publish_block(
            self._block_builder.block_header)

    def _sign_block(self, block, identity_signer):
        """ The block should be complete and the final
        signature from the publishing validator(this validator) needs to
        be added.
        :param block: the Block to sign.
        :param identity_signer: the singer to sign the block with.
        """
        header_bytes = block.block_header.SerializeToString()
        signature = identity_signer.sign(header_bytes)
        block.set_signature(signature)

    def finalize_block_complete(self,consensus):
        # proxy reply
        LOGGER.debug("_CandidateBlock::finalize_block_complete for BRANCH=%s",self._identifier[:8])
        self._consensus.finalize_block_complete(consensus)

    def finalize_block(self, identity_signer, pending_batches):
        """Compose the final Block to publish. This involves flushing
        the scheduler, having consensus bless the block, and signing
        the block.
        :param identity_signer: the cryptographic signer to sign the block
            with.
        :param pending_batches: list to receive any batches that were
        submitted to add to the block but were not validated before this
        call.
        :return: The generated Block, or None if Block failed to finalize.
        In both cases the pending_batches will contain the list of batches
        that need to be added to the next Block that is built.
        """
        LOGGER.debug("_CandidateBlock::finalize_block for BRANCH=%s", self._identifier[:8])
        self._scheduler.unschedule_incomplete_batches()
        self._scheduler.finalize()
        self._scheduler.complete(block=True)

        # this is a transaction cache to track the transactions committed
        # up to this batch. Only valid transactions that were processed
        # by the scheduler are added.
        committed_txn_cache = TransactionCommitCache(self._block_store)

        builder = self._block_builder
        bad_batches = []  # the list of batches that failed processing
        state_hash = None

        # Walk the pending batch list:
        # - find the state hash for the block, the block state_hash is
        # is randomly placed on one of the transactions, so must interogate
        # every batch to find it. If it is on a batch that failed processing
        # then this block will be abandoned.
        # - build three lists of batches:
        # 1) a lists of all valid transactions that will be included in the
        #   block, these are added to the BlockBuilder to include in the Block
        # 2) all batches that were not executed, these are to be returned
        #   in the pending_batches list
        # 3) all batches that failed processing. These will be discarded.
        #   This list is needed in some case when the block is abandoned to
        #   make sure they do not remain in the pending_batches list.
        for batch in self._pending_batches:
            if batch.trace:
                LOGGER.debug("TRACE %s: %s", batch.header_signature,self.__class__.__name__)

            result = self._scheduler.get_batch_execution_result(batch.header_signature)
            # if a result is None, this means that the executor never
            # received the batch and it should be added to
            # the pending_batches, to be added to the next
            # block
            if result is None:
                # If this was an injected batch, don't keep it in pending
                # batches since it had to be in this block
                if batch.header_signature not in self._injected_batch_ids:
                    pending_batches.append(batch)
                else:
                    LOGGER.warning("Failed to inject batch '%s'", batch.header_signature)
            elif result.is_valid:
                # check if a dependent batch failed. This could be belt and
                # suspenders action here but it is logically possible that
                # a transaction has a dependency that fails it could
                # still succeed validation. In which case we do not want
                # to add it to the batch.
                if not self._check_batch_dependencies(batch,committed_txn_cache):
                    LOGGER.debug("Batch %s invalid, due to missing txn dependency.", batch.header_signature)
                    LOGGER.debug("Abandoning block %s: root state hash has invalid txn applied",builder)
                    # Update the pending batch list to be all the
                    # batches that passed validation to this point and
                    # none of the ones that failed. It is possible that
                    # this batch caused a future batch to fail so
                    # we leave all of the batches that failed after this
                    # one in the list.
                    bad_batches.append(batch)
                    pending_batches.clear()
                    pending_batches.extend([
                        x for x in self._pending_batches
                        if x not in bad_batches
                    ])
                    return None
                else:
                    builder.add_batch(batch)
                    committed_txn_cache.add_batch(batch)
                if result.state_hash is not None:
                    state_hash = result.state_hash
            else:
                bad_batches.append(batch)
                LOGGER.debug("Batch %s invalid, not added to block.",
                             batch.header_signature)

        if state_hash is None or not builder.batches:
            LOGGER.debug("Abandoning block %s: no batches added", builder)
            return None
        """
        After this point in case PROXY consensus we should inform consensus engine about possibility finalize block
        """
        LOGGER.debug("_CandidateBlock:: _consensus.finalize_block()\n")
        if not self._consensus.finalize_block(builder.block_header):
            LOGGER.debug("Abandoning block %s, consensus failed to finalize it", builder)
            # return all valid batches to the pending_batches list
            pending_batches.clear()
            pending_batches.extend([x for x in self._pending_batches
                                    if x not in bad_batches])
            return None
        LOGGER.debug("_CandidateBlock:: _consensus.finalize_block() DONE state_hash=%s\n",state_hash)
        builder.set_state_hash(state_hash)
        self._sign_block(builder, identity_signer)
        return builder.build_block()


class BlockPublisher(object):
    """
    Responsible for generating new blocks and publishing them when the
    Consensus deems it appropriate.
    """

    def __init__(self,
                 transaction_executor,
                 block_cache,
                 state_view_factory,
                 settings_cache,
                 block_sender,
                 batch_sender,
                 squash_handler,
                 chain_head,
                 identity_signer,
                 data_dir,
                 config_dir,
                 permission_verifier,
                 check_publish_block_frequency,
                 batch_observers,
                 batch_injector_factory=None,
                 metrics_registry=None,
                 consensus_notifier=None):
        """
        Initialize the BlockPublisher object

        Args:
            transaction_executor (:obj:`TransactionExecutor`): A
                TransactionExecutor instance.
            block_cache (:obj:`BlockCache`): A BlockCache instance.
            state_view_factory (:obj:`StateViewFactory`): StateViewFactory for
                read-only state views.
            block_sender (:obj:`BlockSender`): The BlockSender instance.
            batch_sender (:obj:`BatchSender`): The BatchSender instance.
            squash_handler (function): Squash handler function for merging
                contexts.
            chain_head (:obj:`BlockWrapper`): The initial chain head.
            identity_signer (:obj:`Signer`): Cryptographic signer for signing
                blocks
            data_dir (str): path to location where persistent data for the
                consensus module can be stored.
            config_dir (str): path to location where configuration can be
                found.
            batch_injector_factory (:obj:`BatchInjectorFatctory`): A factory
                for creating BatchInjectors.
            metrics_registry (MetricsRegistry): Metrics registry used to
                create pending batch gauge
        """
        self._lock = RLock()
        self._proxy_lock = RLock() # for external consensus
        """
        for modern proxy consensus -
        wait until external engine  ask block candidate for one of the DAG's branch - 
        """  
        self._engine_ask_candidate = {}
        self._blocks_summarize = [] # list of blocks which could be summarized
        self._consensus_notifier = consensus_notifier
        self._consensus = None # for external consensus name
        self._candidate_blocks = {} # all active branches - for DAG version only 
        self._candidate_block = None  # _CandidateBlock helper,
        self._chain_heads = {}
        # the next block in potential chain
        self._block_cache = block_cache
        self._block_store = block_cache.block_store
        self._state_view_factory = state_view_factory
        self._settings_cache = settings_cache
        self._transaction_executor = transaction_executor
        self._block_sender = block_sender
        self._batch_publisher = BatchPublisher(identity_signer, batch_sender)
        self._pending_batches = []  # batches we are waiting for validation,
        # arranged in the order of batches received.
        self._pending_batch_ids = []
        self._publish_count_average = _RollingAverage(
            NUM_PUBLISH_COUNT_SAMPLES, INITIAL_PUBLISH_COUNT)

        self._chain_head = chain_head  # block (BlockWrapper)
        self._squash_handler = squash_handler
        self._identity_signer = identity_signer
        self._data_dir = data_dir
        self._config_dir = config_dir
        self._permission_verifier = permission_verifier
        self._batch_injector_factory = batch_injector_factory

        # For metric gathering
        if metrics_registry:
            self._pending_batch_gauge = GaugeWrapper(
                metrics_registry.gauge('pending_batch_gauge'))
            self._blocks_published_count = CounterWrapper(
                metrics_registry.counter('blocks_published_count'))
        else:
            self._blocks_published_count = CounterWrapper()
            self._pending_batch_gauge = GaugeWrapper()

        self._batch_queue = queue.Queue()
        self._queued_batch_ids = []
        self._batch_observers = batch_observers
        self._check_publish_block_frequency = check_publish_block_frequency
        self._publisher_thread = None
        LOGGER.debug("BlockPublisher: INIT chain_head=%s block_store=%s\n",chain_head,type(self._block_store))

    def start(self):
        self._publisher_thread = _PublisherThread(
            block_publisher=self,
            batch_queue=self._batch_queue,
            check_publish_block_frequency=self._check_publish_block_frequency)
        LOGGER.debug("BlockPublisher: start _PublisherThread")
        self._publisher_thread.start()

    def stop(self):
        if self._publisher_thread is not None:
            self._publisher_thread.stop()
            self._publisher_thread = None

    def queue_batch(self, batch):
        """
        New batch has been received, queue it with the BlockPublisher for
        inclusion in the next block.
        """
        LOGGER.debug("BlockPublisher::queue_batch ADD new batch=%s",batch.header_signature)
        self._batch_queue.put(batch)
        self._queued_batch_ids.append(batch.header_signature)
        for observer in self._batch_observers:
            observer.notify_batch_pending(batch)

    def can_accept_batch(self):
        return len(self._pending_batches) < self._get_current_queue_limit()

    def _get_current_queue_limit(self):
        # Limit the number of batches to 2 times the publishing average.  This
        # allows the queue to grow geometrically, if the queue is drained.
        return 2 * self._publish_count_average.value

    def get_current_queue_info(self):
        """Returns a tuple of the current size of the pending batch queue
        and the current queue limit.
        """
        return (len(self._pending_batches), self._get_current_queue_limit())

    @property
    def chain_head_lock(self):
        return self._lock

    def _build_candidate_block(self, chain_head):
        """ Build a candidate block and construct the consensus object to
        validate it.
        :param chain_head: The block to build on top of.
        :return: (BlockBuilder) - The candidate block in a BlockBuilder
        wrapper.
        For DAG build candidate for chain_head.identifier branch
        """
        main_head = self._block_cache.block_store.chain_head
        LOGGER.debug("BlockPublisher: BUILD CANDIDATE_BLOCK for BRANCH=%s:%s main_head=%s",chain_head.block_num,chain_head.identifier[:8],main_head.block_num)
        
        state_view = BlockWrapper.state_view_for_block(main_head,self._state_view_factory) # FOR DAG use main_head instead chain_head
        consensus_module,consensus_name = ConsensusFactory.try_configured_consensus_module(chain_head.header_signature,state_view)
        if not consensus_module:
            # there is no internal consensus 
            # check may consensus engine already was registred
            LOGGER.debug("BlockPublisher:_build_candidate_block no internal consensus_module=%s",consensus_name)
            if not self._consensus_notifier.was_registered_engine(consensus_name):
                raise NotRegisteredConsensusModule
            """ 
            External consensus was registered.Maybe create fake consensus module?
            """
            self._consensus = consensus_name[0] # save consensus name
            consensus_module = ConsensusFactory.try_configured_proxy_consensus()
            LOGGER.debug("BlockPublisher:_build_candidate_block External consensus was registered=%s",consensus_name)
        bid = chain_head.identifier
        LOGGER.debug("BlockPublisher: BUILD CANDIDATE_BLOCK for[%s]=%s consensus_module=(%s) ask_candidate=%s",chain_head.block_num,bid[:8],consensus_name,self._engine_ask_candidate)
        # using chain_head so so we can use the setting_cache
        max_batches = int(self._settings_cache.get_setting(
            'sawtooth.publisher.max_batches_per_block',
            main_head.state_root_hash,# for DAG  chain_head.state_root_hash,
            default_value=0))

        public_key = self._identity_signer.get_public_key().as_hex()
        consensus = consensus_module.\
            BlockPublisher(block_cache=self._block_cache,
                           state_view_factory=self._state_view_factory,
                           batch_publisher=self._batch_publisher,
                           data_dir=self._data_dir,
                           config_dir=self._config_dir,
                           validator_id=public_key)
        if hasattr(consensus, 'set_publisher'):
            # external proxy consensus
            consensus.set_publisher(self)
            #self._block_summarize = None
            if bid in self._engine_ask_candidate:
                # set consensus
                consensus.set_consensus_name(self._consensus)

        batch_injectors = []
        if self._batch_injector_factory is not None:
            batch_injectors = self._batch_injector_factory.create_injectors(main_head.identifier) # FOR DAG main_head instead of chain_head.identifier
            if batch_injectors:
                LOGGER.debug("Loaded batch injectors: %s", batch_injectors)
        """
        For DAG version we should ask block_num for last node into sorted graph - FIXME
        block_num for new candidate should be more then block_num of its parent
        """
        
        block_num = self._block_store.block_num(chain_head.block_num)
        LOGGER.debug("make header for block (%s:...)->(%s:%s) heads=%s",block_num,chain_head.block_num,chain_head.header_signature[:8],[str(blk.block_num)+':'+key[:8] for key,blk in self._chain_heads.items()])
        block_header = BlockHeader(
            block_num=block_num , # ask last block number from store
            previous_block_id=chain_head.header_signature,
            signer_public_key=public_key)
        block_builder = BlockBuilder(block_header)
        if not consensus.initialize_block(block_builder.block_header):
            # for proxy consensus waiting until reply fron consensus
            # return reserved block num
            LOGGER.debug("Consensus not ready to build candidate block.")
            self._block_store.pop_block_number(block_num)
            return None

        # switch of marker from proxy engine
        del self._engine_ask_candidate[bid] 
        # create a new scheduler
        # for DAG we should use state_root_hash from head with max number
        main_head = self._block_cache.block_store.chain_head
        LOGGER.debug("Use BLOCK=%s ROOT STATE=%s for _transaction_executor",main_head.block_num,main_head.state_root_hash[:10])
        scheduler = self._transaction_executor.create_scheduler(self._squash_handler, main_head.state_root_hash)

        # build the TransactionCommitCache
        committed_txn_cache = TransactionCommitCache(
            self._block_cache.block_store)
        LOGGER.debug("_build_candidate_block:  self._transaction_executor.execute(scheduler) parent=%s",bid[:8]) 
        self._transaction_executor.execute(scheduler)
        self._candidate_block = _CandidateBlock(
            self._block_cache.block_store,
            consensus, scheduler,
            committed_txn_cache,
            block_builder,
            max_batches,
            batch_injectors,
            bid)
        # add new candidate into list
        self._candidate_blocks[bid] = self._candidate_block
        LOGGER.debug("NEW candidate block[%s]=%s candidates=%s",self._candidate_block.block_num,bid[:8],[str(blk.block_num)+':'+key[:8] for key,blk in self._candidate_blocks.items()])
        for batch in self._pending_batches:
            if self._candidate_block.can_add_batch:
                self._candidate_block.add_batch(batch)
            else:
                break

    def on_batch_received(self, batch):
        """
        A new batch is received, send it for validation
        :param batch: the new pending batch
        :return: None
        """
        LOGGER.debug("BlockPublisher:on_batch_received (%s)",batch)
        with self._lock:
            self._queued_batch_ids = self._queued_batch_ids[:1]
            if self._permission_verifier.is_batch_signer_authorized(batch):
                self._pending_batches.append(batch)
                self._pending_batch_ids.append(batch.header_signature)
                self._pending_batch_gauge.set_value(len(self._pending_batches))
                # if we are building a block then send schedule it for
                # execution.
                
                LOGGER.debug("BlockPublisher:on_batch_received candidate block's num=%s heads=%s",len(self._candidate_blocks),[str(blk.block_num)+':'+key[:8] for key,blk in self._chain_heads.items()])
                """
                choice block candidate for adding batch from self._candidate_blocks
                FIXME - USE some strategy for choicing candidate
                """
                for candidate in self._candidate_blocks.values():
                    if candidate and candidate.can_add_batch:
                        """
                        there is block candidate and we can add batch into them
                        for DAG we should choice one of the block candidate
                        """
                        LOGGER.debug("BlockPublisher:on_batch_received use condidate=%s from=%s",candidate.identifier[:8],[str(blk.block_num)+':'+key[:8] for key,blk in self._candidate_blocks.items()])
                        candidate.add_batch(batch)
                        break
            else:
                LOGGER.debug("Batch has an unauthorized signer. Batch: %s",batch.header_signature)

    def _rebuild_pending_batches(self, committed_batches, uncommitted_batches):
        """When the chain head is changed. This recomputes the list of pending
        transactions
        :param committed_batches: Batches committed in the current chain
        since the root of the fork switching from.
        :param uncommitted_batches: Batches that were committed in the old
        fork since the common root.
        """
        if committed_batches is None:
            committed_batches = []
        if uncommitted_batches is None:
            uncommitted_batches = []

        committed_set = set([x.header_signature for x in committed_batches])

        pending_batches = self._pending_batches

        self._pending_batches = []
        self._pending_batch_ids = []

        num_committed_batches = len(committed_batches)
        if num_committed_batches > 0:
            # Only update the average if either:
            # a. Not drained below the current average
            # b. Drained the queue, but the queue was not bigger than the
            #    current running average
            remainder = len(self._pending_batches) - num_committed_batches
            if remainder > self._publish_count_average.value or \
                    num_committed_batches > self._publish_count_average.value:
                self._publish_count_average.update(num_committed_batches)

        # Uncommitted and pending disjoint sets
        # since batches can only be committed to a chain once.
        for batch in uncommitted_batches:
            if batch.header_signature not in committed_set:
                self._pending_batches.append(batch)
                self._pending_batch_ids.append(batch.header_signature)

        for batch in pending_batches:
            if batch.header_signature not in committed_set:
                self._pending_batches.append(batch)
                self._pending_batch_ids.append(batch.header_signature)

    def on_chain_updated(self, chain_head,
                         committed_batches=None,
                         uncommitted_batches=None,
                         branch_id=None):
        """
        The existing chain has been updated, the current head block has
        changed.

        :param chain_head: the new head of block_chain, can be None if
        no block publishing is desired.
        :param committed_batches: the set of batches that were committed
         as part of the new chain.
        :param uncommitted_batches: the list of transactions if any that are
        now de-committed when the new chain was selected.
        :return: None
        """
        try:
            with self._lock:
                if chain_head is not None:
                    """
                    call from chain controller for changing head of previous_block_id's branch 
                    also change _chain_heads for branch branch_candidate_id
                    """
                    branch_candidate_id = chain_head.previous_block_id
                    LOGGER.info('Now building on top of block: %s-->%s num branch=%s',branch_candidate_id[:8],chain_head.identifier[:8],len(self._chain_heads))
                    if branch_candidate_id in self._chain_heads:
                        del self._chain_heads[branch_candidate_id]
                        LOGGER.info('DEL HEAD for DAG branch=%s\n',branch_candidate_id[:8])
                    # update head for DAG branch
                    self._chain_heads[chain_head.identifier] = chain_head
                    
                else:
                    """
                    for DAG suspended only for current branch 
                    clean _chain_heads for branch_id
                    """
                    branch_candidate_id = branch_id
                    LOGGER.info('Block publishing is suspended until new chain head for %s arrives.',branch_id[:8])

                if branch_candidate_id in self._candidate_blocks:
                    LOGGER.info('Update DAG branch head for ID=%s heads=%s\n',branch_candidate_id[:8],[key[:8] for key in self._chain_heads.keys()])
                    del self._candidate_blocks[branch_candidate_id]

                """
                for DAG we can have many heads and for each of them we should have candidate block
                chain_head is new position into branch  
                also we should have a list of chain_head and correct item which is corresponding with chain_head.previous_block_id
                """
                self._chain_head = chain_head
                """
                for DAG we should clean block candidate only for current branch 
                """
                self._candidate_block = None  # we need to make a new
                # _CandidateBlock (if we can) since the block chain has updated
                # under us.
                if chain_head is not None:
                    self._rebuild_pending_batches(committed_batches,uncommitted_batches)
                    """
                    We can check is internal or external consensus present and if there is one of them build candidate for branch
                    """
                    try:
                        self._build_candidate_block(chain_head)
                    except NotRegisteredConsensusModule:
                        """
                        we should do it after request from consensus engine
                        """
                        LOGGER.debug("BlockPublisher: CANT BUILD BLOCK CANDIDATE (WAIT consensus engine)\n")

                    
                    self._pending_batch_gauge.set_value(len(self._pending_batches))

        # pylint: disable=broad-except
        except Exception as exc:
            LOGGER.critical("on_chain_updated exception.")
            LOGGER.exception(exc)

    def on_check_publish_block(self, force=False):
        """Ask the consensus module if it is time to claim the candidate block
        if it is then, claim it and tell the world about it.
        :return:
            None
        """
        #LOGGER.debug("BlockPublisher:on_check_publish_block ...")
        """
        periodicaly ask publish block for current candidate
        """
        try:
            with self._lock:
                # go through  _chain_heads and create block candidate
                for hid,head in self._chain_heads.items():
                    if (hid not in self._candidate_blocks 
                        and hid in self._engine_ask_candidate
                        and self._pending_batches):
                        # for case when block candidate was dropped by mistakes
                        LOGGER.debug("BlockPublisher: on_check_publish_block BUILD CANDIDATE BLOCK for head=%d\n",hid[:8])
                        self._build_candidate_block(head)
                """
                # old version
                if (self._chain_head is not None
                        and self._candidate_block is None
                        and self._chain_head.identifier in self._engine_ask_candidate 
                        and self._pending_batches):
                    LOGGER.debug("BlockPublisher: on_check_publish_block BUILD CANDIDATE BLOCK\n")
                    self._build_candidate_block(self._chain_head)
                """

                """
                for DAG we should check all branches here and try to publish it for chain controller
                """
                for bid,candidate in list(self._candidate_blocks.items()):
                    #LOGGER.debug("BlockPublisher: check candidate=%s",bid[:8])
                    if (force or candidate.has_pending_batches()) and candidate.check_publish_block():
                    
                        pending_batches = []  # will receive the list of batches
                        # that were not added to the block
                        last_batch = candidate.last_batch
                        LOGGER.debug("BlockPublisher: before finalize_block batchs=%s for BRANCH=%s\n",len(pending_batches),bid[:8])
                        block = candidate.finalize_block(self._identity_signer,pending_batches)
                        LOGGER.debug("BlockPublisher: after finalize_block batchs=%s block=%s",len(self._pending_batches),block is not None)

                        self._candidate_block = None
                    
                        # Update the _pending_batches to reflect what we learned.
                    
                        last_batch_index = self._pending_batches.index(last_batch)
                        unsent_batches = self._pending_batches[last_batch_index + 1:]
                        self._pending_batches = pending_batches + unsent_batches
                    
                        self._pending_batch_gauge.set_value(len(self._pending_batches))
                    
                        if block:
                            blkw = BlockWrapper(block)
                            LOGGER.info("Claimed Block: for branch=%s (%s)",blkw.identifier[:8],block)
                            """
                            send block to chain controller where we will do consensus
                            external engine after this moment will be waiting NEW BLOCK message
                            """
                            self._block_sender.send(blkw.block)
                            self._blocks_published_count.inc()
                    
                            # We built our candidate, disable processing until
                            # the chain head is updated. Only set this if
                            # we succeeded. Otherwise try again, this
                            # can happen in cases where txn dependencies
                            # did not validate when building the block.
                            LOGGER.info("on_check_publish_block: on_chain_updated(None) BRANCH=%s",bid[:8])
                            """
                            for DAG we stop processing only for this branch (self._candidate_block.identifier) 
                            send branch id as additional argument for on_chain_updated()
                            """
                            self.on_chain_updated(None,branch_id=bid)
                            LOGGER.info("on_check_publish_block: after update candidates=%s heads=%s",[key[:8] for key in self._candidate_blocks.keys()],[key[:8] for key in self._chain_heads.keys()])
                        else:
                            """
                            candidate.finalize_block() return None but external consensus don't know about this and use bid for reply summarize()
                            so we should create new candidate for this BID in this function
                            also _chain_heads has head for branch bid
                            """ 
                            LOGGER.info("on_check_publish_block: was not finalize branch=%s",bid[:8])
                            self._engine_ask_candidate[bid] = True
                            del self._candidate_blocks[bid]


        # pylint: disable=broad-except
        except Exception as exc:
            LOGGER.critical("on_check_publish_block exception.")
            LOGGER.exception(exc)

    def has_batch(self, batch_id):
        with self._lock:
            if batch_id in self._pending_batch_ids:
                return True
            if batch_id in self._queued_batch_ids:
                return True

        return False
    """
    for proxy consensus interface
    """
    def on_head_updated(self,hid,new_hid,chain_head):
        with self._lock:
            # update head of branch
            del self._chain_heads[hid]
            self._chain_heads[new_hid] = chain_head
            LOGGER.info('UPDATE HEAD for branch=%s heads=%s\n',hid[:8],[str(blk.block_num)+':'+key[:8] for key,blk in self._chain_heads.items()])
            

    def on_initialize_build_candidate(self, chain_head = None):
        """
        build only after request from consensus engine and for chain_head only 
        external consensus have got chain_head via chain_head_get()     
        """
        try:
            with self._lock:
                if chain_head is not None:
                    #self._chain_head = chain_head
                    LOGGER.info('on_initialize_build_candidate: parent=%s heads=%s', chain_head.identifier[:8],[str(blk.block_num)+':'+key[:8] for key,blk in self._chain_heads.items()])
                    self._build_candidate_block(chain_head)

        # pylint: disable=broad-except
        except Exception as exc:
            LOGGER.critical("on_initialize_build_candidate exception.")
            LOGGER.exception(exc)

    def on_finalize_block(self,block_header):
        # add block for summarizing - call from chain controller
        with self._proxy_lock:
            self._blocks_summarize.append((block_header.consensus,block_header.previous_block_id)) 
            
        LOGGER.debug('BlockPublisher: on_finalize_block  parent block=%s cnt=%s',block_header.previous_block_id[:8],len(self._blocks_summarize))
        # try to wait until proxy.finalize_block

    def initialize_block(self, block):
        """
        we are know parent's ID from chain_head_get()
        """
        LOGGER.debug('BlockPublisher: initialize_block for parent[%s]=%s\n',block.block_num, block.identifier[:8])
        """
        self._py_call('initialize_block', ctypes.py_object(block))
        """
        self._engine_ask_candidate[block.identifier] = True
        self._can_print_summarize = True
        self.on_initialize_build_candidate(block)
        
        #raise BlockInProgress

    def summarize_block(self, force=False):
        """
        call from ConsensusSummarizeBlockHandler
        for DAG we should check all dag header and return one of them 
        
        """
        
        """
        (vec_ptr, vec_len, vec_cap) = ffi.prepare_vec_result()
        self._call(
            'summarize_block',
            ctypes.c_bool(force),
            ctypes.byref(vec_ptr),
            ctypes.byref(vec_len),
            ctypes.byref(vec_cap))

        return ffi.from_rust_vec(vec_ptr, vec_len, vec_cap)
        """
        #LOGGER.debug('BlockPublisher: summarize_block ...')
        with self._proxy_lock:
            if len(self._blocks_summarize) == 0:
                if self._can_print_summarize:
                    self._can_print_summarize = False
                    LOGGER.debug('BlockPublisher: summarize_block BLOCK EMPTY self=%s',self)
                raise BlockEmpty #BlockNotReady
            # return one of the elements
            elem = self._blocks_summarize.pop()

        # elem[1] THIS IS PARENT OF BLOCK CANDIDATE
        LOGGER.debug('BlockPublisher: summarize_block id=%s',elem[1][:8])
        return elem
        

    def finalize_block(self, consensus=None,block_id=None, force=False):
        """
        at this point we should continue _candidate_block.finalize_block
        """
        bid = block_id.hex() 
        LOGGER.debug('BlockPublisher: finalize_block consensus=%s branch=%s',consensus,bid[:8])
        if bid in self._candidate_blocks:
            candidate = self._candidate_blocks[bid]
            LOGGER.debug('BlockPublisher: compare candidate=%s',candidate==self._candidate_block)
        else:
            raise BlockNotInitialized
            

        # now we can send block to chain controller
        # 
        candidate.finalize_block_complete(consensus)
        """
        (vec_ptr, vec_len, vec_cap) = ffi.prepare_vec_result()
        self._call(
            'finalize_block',
            consensus, len(consensus),
            ctypes.c_bool(force),
            ctypes.byref(vec_ptr),
            ctypes.byref(vec_len),
            ctypes.byref(vec_cap))

        return ffi.from_rust_vec(vec_ptr, vec_len, vec_cap).decode('utf-8')
        """
        LOGGER.debug('BlockPublisher: finalize_block send reply candidate=%s',candidate is not None)
        # return parent block id 
        return bid 

    def cancel_block(self,branch_id=None):
        """
        cancel block only for branch 
        """
        bid = branch_id.hex() 
        LOGGER.debug('BlockPublisher:cancel_block ASK cancel for BRANCH=%s num=%s',bid[:8],len(self._candidate_blocks))
        if bid in self._candidate_blocks:
            LOGGER.debug('BlockPublisher:cancel_block DO cancel for BRANCH=%s',bid[:8])
        if self._candidate_block is not None:
            LOGGER.debug('BlockPublisher:cancel_block Stop adding batches to the current block and abandon it')
            # need new block candidate
            self._candidate_block = None

        """
        self._call("cancel_block")
        """

class _RollingAverage(object):

    def __init__(self, sample_size, initial_value):
        self._samples = deque(maxlen=sample_size)

        self._samples.append(initial_value)
        self._current_average = initial_value

    @property
    def value(self):
        return self._current_average

    def update(self, sample):
        """Add the sample and return the updated average.
        """
        self._samples.append(sample)

        self._current_average = sum(self._samples) / len(self._samples)

        return self._current_average

class BlockEmpty(Exception):
    """There are no batches in the block."""

class BlockInProgress(Exception):
    """There is already a block in progress."""


class BlockNotInitialized(Exception):
    """There is no block in progress to finalize."""


class MissingPredecessor(Exception):
    """A predecessor was missing"""


