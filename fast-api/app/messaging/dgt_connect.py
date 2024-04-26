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

