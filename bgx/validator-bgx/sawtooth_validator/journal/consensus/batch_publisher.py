# Copyright 2017 DGT NETWORK INC 
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

from sawtooth_validator.protobuf.batch_pb2 import Batch,BatchList
from sawtooth_validator.protobuf.batch_pb2 import BatchHeader
import time

class BatchPublisher(object):
    """ Utility class to help BlockPublisher provide transaction publishing
    services to the consensus implementations.
    """

    def __init__(self, identity_signer, batch_sender):
        """Initialize the BatchPublisher.
        :param identity_signer: the validator's cryptographic signer.
        :param batch_sender: interface to an object that will post the built
        batch to the network.
        """
        self._batch_sender = batch_sender
        self._identity_signer = identity_signer

    @property
    def identity_signer(self):
        return self._identity_signer

    def send(self, transactions):
        """ Package up transactions into a batch and send them to the
        network via the provided batch_sender.
        :param transactions: list of transactions to package and broadcast.
        :return: None
        """
        txn_signatures = [txn.header_signature for txn in transactions]
        header = BatchHeader(
            signer_public_key=self._identity_signer.get_public_key().as_hex(),
            transaction_ids=txn_signatures
        ).SerializeToString()

        signature = self._identity_signer.sign(header)
        batch = Batch(
            header=header,
            transactions=transactions,
            header_signature=signature,timestamp=int(time.time()))

        self._batch_sender.send(batch)

    def send_batch(self,batch,candidate_id=None):
        self._batch_sender.send_batch(batch,candidate_id)

    def send_batches(self,batches,candidate_id=None,block_num=None):
        batch_list = BatchList(candidate_id=bytes.fromhex(candidate_id) if candidate_id is not None else None,
                               block_num=block_num
                               )
        batch_list.batches.extend(batches)

        self._batch_sender.send_batches(batch_list)

