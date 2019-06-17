# Copyright 2018 Intel Corporation
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


from collections import namedtuple

from sawtooth_validator.protobuf.block_pb2 import BlockHeader
from sawtooth_validator.journal.block_wrapper import BlockWrapper
from sawtooth_validator.journal.block_wrapper import BlockStatus

import logging
LOGGER = logging.getLogger(__name__)

class UnknownBlock(Exception):
    """The given block could not be found."""


StartupInfo = namedtuple(
    'SignupInfo',
    ['chain_head', 'peers', 'local_peer_info'])


class ConsensusProxy:
    """Receives requests from the consensus engine handlers and delegates them
    to the appropriate components."""

    def __init__(self, block_manager, block_publisher,
                 chain_controller, gossip, identity_signer,
                 settings_view_factory, state_view_factory):

        self._block_manager = block_manager
        self._chain_controller = chain_controller
        self._block_publisher = block_publisher
        self._gossip = gossip
        self._identity_signer = identity_signer
        self._public_key = self._identity_signer.get_public_key().as_bytes()
        self._settings_view_factory = settings_view_factory
        self._state_view_factory = state_view_factory

    def register(self):
        chain_head = self._chain_controller.chain_head
        if chain_head is None:
            return None

        return StartupInfo(
            chain_head=chain_head,
            peers=[
                self._gossip.peer_to_public_key(peer)
                for peer in self._gossip.get_peers()
            ],
            local_peer_info=self._public_key)

    # Using network service
    def send_to(self, peer_id, message):
        self._gossip.send_consensus_message(
            peer_id=peer_id.hex(),
            message=message,
            public_key=self._public_key)

    def broadcast(self, message):
        self._gossip.broadcast_consensus_message(
            message=message,
            public_key=self._public_key)

    # Using block publisher
    def initialize_block(self, previous_id):
        if previous_id:
            try:
                
                LOGGER.debug("ConsensusProxy:initialize_block (%s)",previous_id.hex())
                #has = self._chain_controller.has_block(previous_id.hex())
                #previous_block1 = self._chain_controller.get_block_from_cache(previous_id.hex()) if has else None
                block = next(self._block_manager.get([previous_id.hex()])) 
                previous_block = BlockWrapper(block=block, status=BlockStatus.Unknown)
                #LOGGER.debug("ConsensusProxy:initialize_block previous_block=(%s~%s)",type(previous_block),type(previous_block1))
                
            except StopIteration:
                raise UnknownBlock()
            
            self._block_publisher.initialize_block(previous_block)
        else:
            self._block_publisher.initialize_block(self._chain_controller.chain_head)

    def summarize_block(self):
        return self._block_publisher.summarize_block()

    def finalize_block(self, consensus_data,block_id):
        return bytes.fromhex(self._block_publisher.finalize_block(consensus=consensus_data,block_id=block_id))

    def cancel_block(self):
        self._block_publisher.cancel_block()

    def check_blocks(self, block_ids):
        for block_id in block_ids:
            if block_id.hex() not in self._block_manager:
                raise UnknownBlock(block_id.hex())
            # say chain controller 
            self._chain_controller.on_check_block(block_id)

    def get_block_statuses(self, block_ids):
        """Returns a list of tuples of (block id, BlockStatus) pairs.
        """
        try:
            return [
                (block_id.hex(),
                 self._chain_controller.block_validation_result(
                     block_id.hex()))
                for block_id in block_ids
            ]
        except KeyError as key_error:
            raise UnknownBlock(key_error.args[0])

    def commit_block(self, block_id):
        LOGGER.debug("ConsensusProxy:commit_block %s",block_id)
        """
        try:
            block = next(self._block_manager.get([block_id.hex()]))
        except StopIteration as stop_iteration:
            raise UnknownBlock(stop_iteration.args[0])
        """
        self._chain_controller.commit_block(block_id) # (block)

    def ignore_block(self, block_id):
        """
        try:
            block = next(self._block_manager.get([block_id.hex()]))
        except StopIteration:
            raise UnknownBlock()
        """
        self._chain_controller.ignore_block(block_id) # (block)

    def fail_block(self, block_id):
        """
        try:
            block = next(self._block_manager.get([block_id.hex()]))
        except StopIteration:
            raise UnknownBlock()
        """
        self._chain_controller.fail_block(block_id) # (block)

    # Using blockstore and state database
    def blocks_get(self, block_ids):
        '''Returns a list of blocks.'''
        return self._get_blocks([block_id.hex() for block_id in block_ids])

    def chain_head_get(self,parent_id=None):
        """
        Returns the main chain head in case parent_id == None.
        and new branch in case parent_id is not None
        """
        
        chain_head = self._chain_controller.chain_head
        LOGGER.debug("ConsensusProxy:chain_head_get head=%s for=%s\n",chain_head,parent_id)
        if chain_head is None:
            raise UnknownBlock()

        return chain_head

    def settings_get(self, block_id, settings):
        '''Returns a list of key/value pairs (str, str).'''

        block = self._get_blocks([block_id.hex()])[0]

        block_header = BlockHeader()
        block_header.ParseFromString(block.header)

        settings_view = self._settings_view_factory.create_settings_view(
            block_header.state_root_hash)

        result = []
        for setting in settings:
            try:
                value = settings_view.get_setting(setting)
            except KeyError:
                # if the key is missing, leave it out of the response
                continue

            result.append((setting, value))

        return result

    def state_get(self, block_id, addresses):
        '''Returns a list of address/data pairs (str, bytes)'''
        block = self._get_blocks([block_id.hex()])[0]
        block_header = BlockHeader()
        block_header.ParseFromString(block.header)

        state_view = self._state_view_factory.create_view(
            block_header.state_root_hash)

        result = []

        for address in addresses:
            # a fully specified address
            if len(address) == 70:
                try:
                    value = state_view.get(address)
                except KeyError:
                    # if the key is missing, leave it out of the response
                    continue

                result.append((address, value))
                continue

            # an address prefix
            leaves = state_view.leaves(address)

            for leaf in leaves:
                result.append(leaf)

        return result

    def _get_blocks(self, block_ids):
        LOGGER.debug("ConsensusProxy:_get_blocks %s\n",block_ids)
        block_iter = self._block_manager.get(block_ids)
        blocks = [b for b in block_iter]
        #blocks = self._chain_controller.get_blocks_validation(block_ids)
        if len(blocks) != len(block_ids):
            LOGGER.debug("ConsensusProxy:_get_blocks UnknownBlock")
            raise UnknownBlock()

        return blocks
