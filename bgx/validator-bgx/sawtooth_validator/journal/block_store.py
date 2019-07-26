# Copyright 2016 Intel Corporation
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

# pylint: disable=no-name-in-module
import logging
from collections.abc import MutableMapping

from sawtooth_validator.journal.block_wrapper import BlockStatus
from sawtooth_validator.journal.block_wrapper import BlockWrapper
from sawtooth_validator.protobuf.block_pb2 import Block
from sawtooth_validator.state.merkle import MerkleDatabase,INIT_ROOT_KEY
LOGGER = logging.getLogger(__name__)

class BlockStore(MutableMapping):
    """
    A dict like interface wrapper around the block store to guarantee,
    objects are correctly wrapped and unwrapped as they are stored and
    retrieved.
    """

    def __init__(self, block_db):
        self._block_store = block_db
        self._chain_heads = {} # for DAG
        self._block_nums  = [] # for DAG - list of reserved block candidate number  
        self._free_block_nums  = [] # for DAG - list of free block number's 
    def __setitem__(self, key, value):
        if key != value.identifier:
            raise KeyError(
                "Invalid key to store block under: {} expected {}".format(
                    key, value.identifier))
        self._block_store.put(key, value)

    def __getitem__(self, key):
        return self._get_block(key)

    def __delitem__(self, key):
        del self._block_store[key]

    def __contains__(self, x):
        return x in self._block_store

    def __iter__(self):
        
        return self.get_block_iter()

    def __len__(self):
        # Required by abstract base class, but implementing is non-trivial
        raise NotImplementedError('BlockStore has no meaningful length')

    def __str__(self):
        out = []
        for key in self._block_store.keys():
            value = self._block_store[key]
            out.append(str(value))
        return ','.join(out)

    @staticmethod
    def create_index_configuration():
        return {
            'batch': BlockStore._batch_index_keys,
            'transaction': BlockStore._transaction_index_keys,
            'block_num': BlockStore._block_num_index_keys,
        }

    @staticmethod
    def deserialize_block(value):
        """
        Deserialize a byte string into a BlockWrapper

        Args:
            value (bytes): the byte string to deserialze

        Returns:
            BlockWrapper: a block wrapper instance
        """
        # Block id strings are stored under batch/txn ids for reference.
        # Only Blocks, not ids or Nones, should be returned by _get_block.
        block = Block()
        block.ParseFromString(value)
        return BlockWrapper(
            status=BlockStatus.Valid,
            block=block)

    @staticmethod
    def serialize_block(blkw):
        """
        Given a block wrapper, produce a byte string

        Args:
            blkw: (:obj:`BlockWrapper`) a block wrapper to serialize

        Returns:
            bytes: the serialized bytes
        """
        return blkw.block.SerializeToString()

    @staticmethod
    def wrap_block(blk):
        return BlockWrapper.wrap(blk)

    def update_chain(self, new_chain, old_chain=None):
        """
        Set the current chain head, does not validate that the block
        store is in a valid state, ie that all the head block and all
        predecessors are in the store.

        :param new_chain: The list of blocks of the new chain.
        :param old_chain: The list of blocks of the existing chain to
            remove from the block store.
        store.
        :return:
        None
        """
        add_pairs = [(blkw.header_signature, blkw) for blkw in new_chain]
        if old_chain:
            del_keys = [blkw.header_signature for blkw in old_chain]
        else:
            del_keys = []

        self._block_store.update(add_pairs, del_keys)

    def add_branch(self,block_id,block):
        # for DAG version - add new branch from block with block_id
        self._chain_heads[block_id] = block

    def update_branch(self,hid,new_hid,block):
        # for DAG version - update branch to another point
        if hid in self._chain_heads:
            del self._chain_heads[hid]
            self._chain_heads[new_hid] = block
            LOGGER.debug("BlockStore: update_branch=%s",hid[:8])

    def update_chain_heads(self,hid,new_block):
        #for DAG only - main head not in _chain_heads
        if hid in self._chain_heads:
            del self._chain_heads[hid]
            self._chain_heads[hid] = new_block
        else:
            # could be for external block

            for key,head in self._chain_heads.items():
                if head.block_num == new_block.block_num:
                    LOGGER.debug("BlockStore: update_chain_heads EXTERNAL del old block=%s.%s",head.block_num,key[:8])
                    del self._chain_heads[key]
                    break
            self._chain_heads[hid] = new_block

    def get_chain_head(self,branch_id):
        # for external block there is no chain head
        return self._chain_heads[branch_id]

    @property
    def chain_heads(self):
        return self._chain_heads

    @property
    def chain_head(self):
        """
        Return the head block of the current chain.
        for DAG return last from sorted node's list
        """
        with self._block_store.cursor(index='block_num') as curs:
            curs.last()
            return curs.value()

    
    def block_num(self,parent_num):
        """
        for DAG version
        Return the last head block of sorted graph and reserve this number because others branch can ask this number
        """
        LOGGER.debug("BlockStore:block_nums=%s free=%s for=%s",self._block_nums,sorted(self._free_block_nums),parent_num)
        if len(self._free_block_nums) > 0 and max(self._free_block_nums) > parent_num:
            for num in sorted(self._free_block_nums):
                if num > parent_num:
                    self._free_block_nums.remove(num)
                    LOGGER.debug("BlockStore: use num=%s free=%s",num,self._free_block_nums)
                    return num

        head = self.chain_head
        LOGGER.debug("BlockStore: find from last=%s",head.block_num)
        block_num = head.block_num + 1
        while block_num in self._block_nums:
            # already reserved by some branch try take next number
            block_num += 1
        # add into reserved list  - taken by candidate
        self._block_nums.append(block_num)
        LOGGER.debug("BlockStore: num=%s block_nums=%s",block_num,self._block_nums)
        return block_num

    def pop_block_number(self,block_num):
        # for external Block pop too because we make ref for external block
        if block_num in self._block_nums:
            self._block_nums.remove(block_num)
            LOGGER.debug("BlockStore:pop_block_number  num=%s nums=%s",block_num,self._block_nums)

    def ref_block_number(self,block_num):
        # for external Block  make ref for block num
        self._block_nums.append(block_num)
        LOGGER.debug("BlockStore:ref_block_number num=%s nums=%s",block_num,self._block_nums)

    def free_block_number(self,block_num):
        # free block number - because block was not validated
        self.pop_block_number(block_num)
        head = self.chain_head
        if block_num < head.block_num + 1:
            # put into free block num list
            self._free_block_nums.append(block_num)
            LOGGER.debug("BlockStore:free_block_number  num=%s nums=%s",block_num,self._free_block_nums)

    def set_global_state_db(self,global_state_db):
        # for DAG - use mercle database for getting root state
        self._global_state_db = global_state_db

    def chain_head_state_root(self):
        """
        Return the state hash of the head block of the current chain.
        FIXME - for DAG use real merkle root state
        """
        chain_head = self.chain_head
        if chain_head is not None:
            return MerkleDatabase.get_real_merkle_root(self._global_state_db)
            #return chain_head.state_root_hash
        return INIT_ROOT_KEY

    @property
    def store(self):
        """
        Access to the underlying store.
        """
        return self._block_store

    def get_predecessor_iter(self, starting_block=None):
        """Returns an iterator that traverses block via its predecesssors.

        Args:
            starting_block (:obj:`BlockWrapper`): the block from which
                traversal begins

        Returns:
            An iterator of block wrappers
        """
        return self.get_block_iter(start_block=starting_block)

    def get_block_iter(self, start_block=None, start_block_num=None,
                       reverse=True):
        """Returns an iterator that traverses blocks in block number order.

        Args:
            start_block (:obj:`BlockWrapper`): the block from which traversal
                begins
            start_block_num (str): a starting block number, in hex, from where
                traversal begins; only used if no starting_block is provided

            reverse (bool): If True, traverse the blocks in from most recent
                to oldest block. Otherwise, it traverse the blocks in the
                opposite order.

        Returns:
            An iterator of block wrappers

        Raises:
            ValueError: If start_block or start_block_num do not specify a
                valid block
        """
        LOGGER.debug("BlockStore: get_block_iter...")
        with self._block_store.cursor(index='block_num') as curs:
            if start_block:
                start_block_num = BlockStore.block_num_to_hex(
                    start_block.block_num)
                if not curs.seek(start_block_num):
                    raise ValueError(
                        'block {} is not a valid block'.format(start_block))
            elif start_block_num:
                if not curs.seek(start_block_num):
                    raise ValueError('Block number {} does not reference a '
                                     'valid block'.format(start_block_num))

            iterator = None
            if reverse:
                iterator = curs.iter_rev()
            else:
                iterator = curs.iter()

            for block in iterator:
                yield block

    @staticmethod
    def _batch_index_keys(block):
        blkw = BlockWrapper.wrap(block)
        return [batch.header_signature.encode()
                for batch in blkw.batches]

    @staticmethod
    def _transaction_index_keys(block):
        blkw = BlockWrapper.wrap(block)
        keys = []
        for batch in blkw.batches:
            for txn in batch.transactions:
                keys.append(txn.header_signature.encode())
        return keys

    @staticmethod
    def _block_num_index_keys(block):
        blkw = BlockWrapper.wrap(block)
        # Format the number to a 64bit hex value, for natural ordering
        return [BlockStore.block_num_to_hex(blkw.block_num).encode()]

    @staticmethod
    def block_num_to_hex(block_num):
        """Converts a block number to a hex string.
        This is used for proper index ordering and lookup.

        Args:
            block_num: uint64

        Returns:
            A hex-encoded str
        """
        return "{0:#0{1}x}".format(block_num, 18)

    def _get_block(self, key):
        value = self._block_store.get(key)
        if value is None:
            raise KeyError('Block "{}" not found in store'.format(key))

        return BlockWrapper.wrap(value)

    def get_blocks(self, block_ids):
        """Returns all blocks with the given set of block_ids.
        If a block id in the provided iterable does not exist in the block
        store, it is ignored.

        Args:
            block_ids (:iterable:str): an iterable of block ids

        Returns
            list of block wrappers found for the given block ids
        """
        return [block for _, block in self._block_store.get_multi(block_ids)]

    def get_block_by_transaction_id(self, txn_id):
        """Returns the block that contains the given transaction id.

        Args:
            txn_id (str): a transaction id

        Returns:
            a block wrapper of the containing block

        Raises:
            ValueError if no block containing the transaction is found
        """
        block = self._block_store.get(txn_id, index='transaction')
        if not block:
            raise ValueError(
                'Transaction "{}" not in BlockStore'.format(txn_id))

        return block

    def get_block_by_number(self, block_num):
        """Returns the block that contains the given transaction id.

        Args:
            block_num (uint64): a block number

        Returns:
            a block wrapper of the containing block

        Raises:
            KeyError if no block with the given number is found
        """
        block = self._block_store.get(
            BlockStore.block_num_to_hex(block_num), index='block_num')
        if not block:
            raise KeyError(
                'Block number "{}" not in BlockStore'.format(block_num))

        return block

    def has_transaction(self, txn_id):
        """Returns True if the transaction is contained in a block in the
        block store.

        Args:
            txn_id (str): a transaction id

        Returns:
            True if it is contained in a committed block, False otherwise
        """
        return self._block_store.contains_key(txn_id, index='transaction')

    def get_block_by_batch_id(self, batch_id):
        """Returns the block that contains the given batch id.

        Args:
            batch_id (str): a batch id

        Returns:
            a block wrapper of the containing block

        Raises:
            ValueError if no block containing the batch is found
        """
        block = self._block_store.get(batch_id, index='batch')
        if not block:
            raise ValueError('Batch "{}" not in BlockStore'.format(batch_id))

        return block

    def get_blocks_by_batch_ids(self, batch_ids):
        """Returns the block that contains the given batch id.

        Args:
            batch_id (str): a batch id

        Returns:
            a block wrapper of the containing block

        Raises:
            ValueError if no block containing the batch is found
        """
        return self._block_store.get_multi(batch_ids, index='batch')

    def has_batch(self, batch_id):
        """Returns True if the batch is contained in a block in the
        block store.

        Args:
            batch_id (str): a batch id

        Returns:
            True if it is contained in a committed block, False otherwise
        """
        return self._block_store.contains_key(batch_id, index='batch')

    def get_batch_by_transaction(self, transaction_id):
        """
        Check to see if the requested transaction_id is in the current chain.
        If so, find the batch that has the transaction referenced by the
        transaction_id and return the batch. This is done by finding the block
        and searching for the batch.

        :param transaction_id (string): The id of the transaction that is being
            requested.
        :return:
        The batch that has the transaction.
        """
        block = self.get_block_by_transaction_id(transaction_id)
        if block is None:
            return None
        # Find batch in block
        for batch in block.batches:
            for txn in batch.transactions:
                if txn.header_signature == transaction_id:
                    return batch
        return None

    def get_batch(self, batch_id):
        """
        Check to see if the requested batch_id is in the current chain. If so,
        find the batch with the batch_id and return it. This is done by
        finding the block and searching for the batch.

        :param batch_id (string): The id of the batch requested.
        :return:
        The batch with the batch_id.
        """
        block = self.get_block_by_batch_id(batch_id)
        return BlockStore._get_batch_from_block(block, batch_id)

    def get_batches(self, batch_ids):
        """Returns a list of committed batches from a iterable of batch ids.
        Any batch id that does not exist in a committed block is ignored.

        Args:
            batch_ids (:iterable:str): the batch ids to find

        Returns:
            A list of the batches found by the given batch ids
        """
        blocks = self._block_store.get_multi(batch_ids, index='batch')

        return [
            BlockStore._get_batch_from_block(block, batch_id)
            for batch_id, block in blocks
        ]

    @staticmethod
    def _get_batch_from_block(block, batch_id):
        for batch in block.batches:
            if batch.header_signature == batch_id:
                return batch

        raise ValueError(
            'Batch {} not in block {}: possible index mismatch'.format(
                batch_id, block.identifier))

    def get_transaction(self, transaction_id):
        """Returns a Transaction object from the block store by its id.

        Params:
            transaction_id (str): The header_signature of the desired txn

        Returns:
            Transaction: The specified transaction

        Raises:
            ValueError: The transaction is not in the block store
        """
        block = self.get_block_by_transaction_id(transaction_id)
        return BlockStore._get_txn_from_block(block, transaction_id)

    def get_transactions(self, transaction_ids):
        blocks = self._block_store.get_multi(transaction_ids,
                                             index='transaction')

        return [
            BlockStore._get_txn_from_block(block, txn_id)
            for txn_id, block in blocks
        ]

    @staticmethod
    def _get_txn_from_block(block, txn_id):
        for batch in block.batches:
            for txn in batch.transactions:
                if txn.header_signature == txn_id:
                    return txn

        raise ValueError(
            'Transaction {} not in block {}: possible index mismatch'.format(
                txn_id, block.identifier))
