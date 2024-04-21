# Copyright 2024 DGT NETWORK INC © Stanislav Parsov
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

import os
import sys
import asyncio
from app.core.config import settings
from app.utils.logger import logger as LOGGER
from zmq.asyncio import ZMQEventLoop
#from .messaging  import Connection

zmq_loop = ZMQEventLoop()
asyncio.set_event_loop(zmq_loop)

#connection = Connection(settings.DGT_CONNECT)
#connection.open()

async def _query_validator(self, request_type, response_proto,payload, error_traps=None):
    """Sends a request to the validator and parses the response.
    """
    LOGGER.debug(
        'Sending %s request to validator',
        self._get_type_name(request_type))

    payload_bytes = payload.SerializeToString()
    response = await self._send_request(request_type, payload_bytes)
    content = self._parse_response(response_proto, response)

    LOGGER.debug(
        'Received %s response from validator with status %s',
        self._get_type_name(response.message_type),
        self._get_status_name(response_proto, content.status))

    self._check_status_errors(response_proto, content, error_traps)
    return self._message_to_dict(content)

async def _send_request(self, request_type, payload):
    """Uses an executor to send an asynchronous ZMQ request to the
    validator with the handler's Connection
    """
    try:
        return await self._connection.send(
            message_type=request_type,
            message_content=payload,
            timeout=self._timeout)
    except DisconnectError:
        LOGGER.warning('Validator disconnected while waiting for response')
        raise errors.ValidatorDisconnected()
    except asyncio.TimeoutError:
        LOGGER.warning('Timed out while waiting for validator response')
        raise errors.ValidatorTimedOut()
    except SendBackoffTimeoutError:
        LOGGER.warning('Failed sending message - Backoff timed out')
        raise errors.SendBackoffTimeout()

async def _head_to_root(self, block_id):
    error_traps = [error_handlers.BlockNotFoundTrap]
    if block_id:
        response = await self._query_validator(
            Message.CLIENT_BLOCK_GET_BY_ID_REQUEST,
            client_block_pb2.ClientBlockGetResponse,
            client_block_pb2.ClientBlockGetByIdRequest(block_id=block_id),
            error_traps)
        block = self._expand_block(response['block'])
    else:
        response = await self._query_validator(
            Message.CLIENT_BLOCK_LIST_REQUEST,
            client_block_pb2.ClientBlockListResponse,
            client_block_pb2.ClientBlockListRequest(
                paging=client_list_control_pb2.ClientPagingControls(
                    limit=1)),
            error_traps)
        block = self._expand_block(response['blocks'][0])
    return (
        block['header_signature'],
        block['header']['state_root_hash'],
    )

@staticmethod
def _parse_response(proto, response):
    """Parses the content from a validator response Message.
    """
    try:
        content = proto()
        content.ParseFromString(response.content)
        return content
    except (DecodeError, AttributeError):
        LOGGER.error('Validator response was not parsable: %s', response)
        raise errors.ValidatorResponseInvalid()

@staticmethod
def _check_status_errors(proto, content, error_traps=None):
    """Raises HTTPErrors based on error statuses sent from validator.
    Checks for common statuses and runs route specific error traps.
    """
    if content.status == proto.OK:
        return

    try:
        if content.status == proto.INTERNAL_ERROR:
            raise errors.UnknownValidatorError()
    except AttributeError:
        # Not every protobuf has every status enum, so pass AttributeErrors
        pass

    try:
        if content.status == proto.NOT_READY:
            raise errors.ValidatorNotReady()
    except AttributeError:
        pass

    try:
        if content.status == proto.NO_ROOT:
            raise errors.HeadNotFound()
    except AttributeError:
        pass

    try:
        if content.status == proto.INVALID_PAGING:
            raise errors.PagingInvalid()
    except AttributeError:
        pass

    try:
        if content.status == proto.INVALID_SORT:
            raise errors.SortInvalid()
    except AttributeError:
        pass

    # Check custom error traps from the particular route message
    if error_traps is not None:
        for trap in error_traps:
            trap.check(content.status)



@staticmethod
def _validate_id(resource_id):
    """Confirms a header_signature is 128 hex characters, raising an
    ApiError if not.
    """
    if not re.fullmatch('[0-9a-f]{,148}', resource_id):  # '[0-9a-f]{128}'
        raise errors.InvalidResourceId(resource_id)

@staticmethod
def _message_to_dict(message):
    """Converts a Protobuf object to a python dict with desired settings.
    """
    return MessageToDict(
        message,
        including_default_value_fields=True,
        preserving_proto_field_name=True)

@staticmethod
def _get_type_name(type_enum):
    return Message.MessageType.Name(type_enum)

@staticmethod
def _get_status_name(proto, status_enum):
    try:
        return proto.Status.Name(status_enum)
    except ValueError:
        return 'Unknown ({})'.format(status_enum)

