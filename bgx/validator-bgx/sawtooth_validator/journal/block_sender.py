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
        self._cluster = None

    def set_cluster(self,cluster):
        # set cluster topology
        self._cluster = cluster
        #self._gossip.set_cluster(cluster)

    def send(self, block):
        """
        use from publisher for sending new block to peers 
        send only own cluster's peer
        """
        exclude = self._gossip.get_exclude(self._cluster) if self._cluster else None

        self._gossip.broadcast_block(block,exclude=exclude)
        self._completer.add_block(block)
