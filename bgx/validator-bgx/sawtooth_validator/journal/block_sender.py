# Copyright 2017 NTRLab
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

import abc


class BlockSender(object, metaclass=abc.ABCMeta):
    """Implementations should take classes like completer,
    and network, and implement a send method that gets called on
    block publish.
    """

    @abc.abstractmethod
    def send(self, block):
        """Sends the block to the completer and also to the
           gossip network.
        :param block:
        :return:
        """
        raise NotImplementedError()


class BroadcastBlockSender(BlockSender):
    def __init__(self, completer, gossip):
        self._completer = completer
        self._gossip = gossip
        self._topology = None
        

    def get_topology(self):
        # set cluster topology
        self._topology = self._gossip.f_topology
        #self._gossip.set_cluster(topology)
        return  self._topology
    def try_to_sync_with_net(self):
        self._gossip.try_to_sync_with_net()

    def send(self, block):
        """
        use from publisher for sending new block to peers 
        send only own cluster's peer
        """
        exclude = self._gossip.get_exclude(self._topology.cluster) if self._topology.cluster else None

        self._gossip.broadcast_block(block,exclude=exclude)
        self._completer.add_block(block)

    def send_arbiter(self, block,arbiter=True):
        """
        use from publisher for sending new block to peers or arbiter 
        we know about arbiters from topology
        """
        if arbiter:
            exclude = self._gossip.get_exclude(self._topology.arbiters) if self._topology.arbiters else None
        else:
            exclude = self._gossip.get_exclude(self._topology.cluster) if self._topology.cluster else None
        self._gossip.broadcast_block(block,exclude=exclude)
        

