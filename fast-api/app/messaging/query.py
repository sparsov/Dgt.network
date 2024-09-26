# Copyright DGT NETWORK INC © Stanislav Parsov  2024
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

import asyncio
import re
import json
import cbor
import base64
from urllib.parse import urlparse
# pylint: disable=no-name-in-module,import-error
# needed for the google.protobuf imports to pass pylint
from google.protobuf.json_format import MessageToDict
from google.protobuf.message import DecodeError
import platform
from pyformance import MetricsRegistry
from pyformance.reporters import InfluxReporter


import app.messaging.exceptions as errors
import app.messaging.error_handlers as error_handlers
from .messaging import DisconnectError
from .messaging import SendBackoffTimeoutError
from .messaging import Connection

from dgt_sdk.protobuf.validator_pb2 import Message
from dgt_sdk.protobuf import client_transaction_pb2
from dgt_sdk.protobuf import client_list_control_pb2
from dgt_sdk.protobuf import client_batch_submit_pb2
from dgt_sdk.protobuf import client_state_pb2
from dgt_sdk.protobuf import client_block_pb2
from dgt_sdk.protobuf import client_batch_pb2
from dgt_sdk.protobuf.client_receipt_pb2 import  ClientReceiptGetRequest
from dgt_sdk.protobuf.client_receipt_pb2 import  ClientReceiptGetResponse
from dgt_sdk.protobuf import client_peers_pb2
from dgt_sdk.protobuf import client_status_pb2
from dgt_sdk.protobuf import client_topology_pb2
from dgt_sdk.protobuf.block_pb2 import BlockHeader
from dgt_sdk.protobuf.batch_pb2 import BatchList
from dgt_sdk.protobuf.batch_pb2 import BatchHeader
from dgt_sdk.protobuf.transaction_pb2 import TransactionHeader
from dgt_sdk.protobuf import client_heads_pb2,client_topology_pb2
from app.core.config import settings
from app.utils.logger import logger as LOGGER
#from dgt_stuff.client_cli.stuff_client import _token_info as stuff_token_info
#from dgt_bgt.client_cli.bgt_client import _token_info as bgt_token_info
# pylint: disable=too-many-lines

DEFAULT_TIMEOUT = 300
FA_PAGE_START = 'page' 
FA_PAGE_LIMIT = 'size' 
PAGE_START = 'start'
PAGE_LIMIT = 'limit'




RUN_STATUSES = {
      "id": "23102b0fcf11e6d6ed0476e08c76dd6ec0a83cf3dba3d77256ede90d048a3545242459efab08627bf622d2da2f1434e48a2e54561df1ada5ba1cc99c02f5c666",
      "invalid_transactions": [
        {
          "id": "5195cd20aa4141605f0172f28b95d041b750d2bc4da5061fda9043089062e75e1020a4cfee46c87e9c09eb6c6be1754502595ae9e0e8790162ff1588148a8f15",
          "message": "Verb is \"dec\", but result would be less than 0"
        }
      ],
      "status": "INVALID"
    }

class MetricsRegistryWrapper():
    def __init__(self, registry):
        self._registry = registry

    def gauge(self, name):
        return self._registry.gauge(
            ''.join([name, ',host=', platform.node()]))

    def counter(self, name):
        return self._registry.counter(
            ''.join([name, ',host=', platform.node()]))

    def timer(self, name):
        return self._registry.timer(
            ''.join([name, ',host=', platform.node()]))
  
      
class CounterWrapper():
    def __init__(self, counter=None):
        self._counter = counter

    def inc(self):
        if self._counter:
            self._counter.inc()


class NoopTimerContext():
    def __enter__(self):
        pass

    def __exit__(self, exception_type, exception_value, traceback):
        pass

    def stop(self):
        pass


class TimerWrapper():
    def __init__(self, timer=None):
        self._timer = timer
        self._noop = NoopTimerContext()

    def time(self):
        if self._timer:
            return self._timer.time()
        return self._noop


class QueryValidatorHandler:
    """Contains a number of aiohttp handlers for endpoints in the Rest Api.

    Each handler takes an aiohttp Request object, and uses the data in
    that request to send Protobuf message to a validator. The Protobuf response
    is then parsed, and finally an aiohttp Response object is sent back
    to the client with JSON formatted data and metadata.

    If something goes wrong, an aiohttp HTTP exception is raised or returned
    instead.

    Args:
        connection (:obj: messaging.Connection): The object that communicates
            with the validator.
        timeout (int, optional): The time in seconds before the Api should
            cancel a request and report that the validator is unavailable.
    """

    def __init__(self,connection,timeout=DEFAULT_TIMEOUT, metrics_registry=None):
        self._connection = connection
        self._timeout = timeout
        if metrics_registry:
            self._post_batches_count = CounterWrapper(
                metrics_registry.counter('post_batches_count'))
            self._post_batches_error = CounterWrapper(
                metrics_registry.counter('post_batches_error'))
            self._post_batches_total_time = TimerWrapper(
                metrics_registry.timer('post_batches_total_time'))
            self._post_batches_validator_time = TimerWrapper(
                metrics_registry.timer('post_batches_validator_time'))
        else:
            self._post_batches_count = CounterWrapper()
            self._post_batches_error = CounterWrapper()
            self._post_batches_total_time = TimerWrapper()
            self._post_batches_validator_time = TimerWrapper()
    def connect(self):
        self._connection.open()
    def disconnect(self):
        self._connection.close()


    async def submit_batches(self, request):
        """Accepts a binary encoded BatchList and submits it to the validator.

        Request:
            body: octet-stream BatchList of one or more Batches
        Response:
            status:
                 - 202: Batches submitted and pending
            link: /batches or /batch_statuses link for submitted batches

        """
        timer_ctx = self._post_batches_total_time.time()
        self._post_batches_count.inc()
        #LOGGER.debug('Submission batches {} ..'.format(timer_ctx))
        # Parse request
        if request.headers['Content-Type'] != 'application/octet-stream':
            LOGGER.debug(
                'Submission headers had wrong Content-Type: %s',
                request.headers['Content-Type'])
            self._post_batches_error.inc()
            raise errors.SubmissionWrongContentType()

        body = await request.read()
        if not body:
            LOGGER.debug('Submission contained an empty body')
            self._post_batches_error.inc()
            raise errors.NoBatchesSubmitted()

        try:
            batch_list = BatchList()
            batch_list.ParseFromString(body)
        except DecodeError:
            LOGGER.debug('Submission body could not be decoded: %s', body)
            self._post_batches_error.inc()
            raise errors.BadProtobufSubmitted()

        # Query validator
        error_traps = [error_handlers.BatchInvalidTrap,
                       error_handlers.BatchQueueFullTrap]
        validator_query = client_batch_submit_pb2.ClientBatchSubmitRequest(
            batches=batch_list.batches)

        with self._post_batches_validator_time.time():
            await self._query_validator(
                Message.CLIENT_BATCH_SUBMIT_REQUEST,
                client_batch_submit_pb2.ClientBatchSubmitResponse,
                validator_query,
                error_traps)

        # Build response envelope
        id_string = ','.join(b.header_signature for b in batch_list.batches)

        status = 202
        link = self._build_url(request, path='/batch_statuses', id=id_string)

        retval = self._wrap_response(
            request,
            metadata={'link': link},
            status=status)

        timer_ctx.stop()
        return retval




    def disclose_receipt(self,data):
        try:                                                                                                                       
            for d in data:                                                                                                         
                for state in d['state_changes']:                                                                                   
                    if 'value' in state:                                                                                           
                        val = state['value']                                                                                       
                        content = cbor.loads(base64.b64decode(val))                                                                
                        for key,v in content.items():                                                                              
                            #dv = cbor.loads(v)                                                                                    
                            try:                                                                                                   
                                token = stuff_token_info(v)                                                                        
                                stuff = cbor.loads(token.stuff)                                                                    
                                stuff['user'] = token.user                                                                         
                            except Exception as ex1:                                                                               
                                token = bgt_token_info(v)                                                                          
                                stuff = {'group_code':token.group_code,'sign':token.sign,'decimals':token.decimals}                
                                                                                                                                   
                            #LOGGER.debug('%s=%s->%s\n',key,v,stuff)                                                               
                            content[key] = stuff                                                                                   
                        state['value'] = content                                                                                   
        except Exception as ex:                                                                                                    
            LOGGER.debug('cant load cbor (%s)\n',ex)                                                                               


    async def validator(self,request):
        """
        change validator
        """
        endpoint = request.query_params.get('endpoint', None) 
        #if endpoint is not None:
        self._connection.reopen(endpoint)
        LOGGER.debug('Request validator endpoint=%s request=%s',endpoint,request)
        return self._wrap_response(
            request,
            data={'endpoint':endpoint}
            )

    async def _query_validator(self, request_type, response_proto,payload, error_traps=None):
        """
           Sends a request to the validator and parses the response.
        """
        LOGGER.debug('Sending %s request to validator',self._get_type_name(request_type))

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
    def _wrap_response(request, data=None, metadata=None, status=200):
        """Creates the JSON response envelope to be sent back to the client.
        """
        envelope = metadata or {}

        if data is not None:
            envelope['data'] = data
        return envelope
        """
        return web.Response(
            status=status,
            content_type='application/json',
            text=json.dumps(
                envelope,
                indent=2,
                separators=(',', ': '),
                sort_keys=True))
        """

    @classmethod
    def _wrap_paginated_response(cls, request, response, controls, data,
                                 head=None):
        """Builds the metadata for a pagingated response and wraps everying in
        a JSON encoded web.Response
        """
        paging_response = response['paging']
        if head is None and 'head_id' in response:
            head = response['head_id']
        link = cls._build_url(
            request,
            head=head,
            start=paging_response['start'],
            limit=paging_response['limit'])

        paging = {}
        limit = controls.get('limit')
        start = controls.get("start")
        paging["limit"] = limit
        paging["start"] = start
        # If there are no resources, there should be nothing else in paging
        if paging_response.get("next") == "":
            return cls._wrap_response(
                request,
                data=data,
                metadata={
                    'head': head,
                    'link': link,
                    'paging': paging
                })

        next_id = paging_response['next']
        paging['next_position'] = next_id

        # Builds paging urls specific to this response
        def build_pg_url(start=None):
            return cls._build_url(request, head=head, limit=limit, start=start)

        paging['next'] = build_pg_url(paging_response['next'])

        return cls._wrap_response(
            request,
            data=data,
            metadata={
                'head': head,
                'link': link,
                'paging': paging
            })

    @classmethod
    def _get_metadata(cls, request, response, head=None):
        """Parses out the head and link properties based on the HTTP Request
        from the client, and the Protobuf response from the validator.
        """
        head = response.get('head_id', head) if response is not None else None
        metadata = {'link': cls._build_url(request, head=head)}

        if head is not None:
            metadata['head'] = head
        return metadata

    @classmethod
    def _build_url(cls, request, path=None, **changes):
        """Builds a response URL by overriding the original queries with
        specified change queries. Change queries set to None will not be used.
        Setting a change query to False will remove it even if there is an
        original query with a value.
        """
        changes = {k: v for k, v in changes.items() if v is not None}
        #queries = {**request.url.query, **changes}
        queries = {**request.query_params, **changes}
        queries = {k: v for k, v in queries.items() if v is not False}
        query_strings = []

        def add_query(key):
            query_strings.append('{}={}'.format(key, queries[key])
                                 if queries[key] != '' else key)

        def del_query(key):
            queries.pop(key, None)

        if 'head' in queries:
            add_query('head')
            del_query('head')

        if 'start' in changes:
            add_query('start')
        elif 'start' in queries:
            add_query('start')

        del_query('start')

        if 'limit' in queries:
            add_query('limit')
            del_query('limit')

        for key in sorted(queries):
            add_query(key)

        scheme = cls._get_forwarded(request, 'proto') or request.url.scheme
        host = cls._get_forwarded(request, 'host') or request.client.host
        port = request.headers.get("X-Forwarded-Port") or request.client.port
        forwarded_path = cls._get_forwarded(request, 'path')
        origin_host  = request.headers.get("host")
        if origin_host :
            
            host = origin_host
        original_uri = request.headers.get("X-Original-URI")
        
        #LOGGER.info('forwarded_proto {}'.format(request.headers))
        if original_uri:
            parsed_uri = urlparse(original_uri)
            orig_path = '/'.join(parsed_uri.path.split('/')[:-1]) 
            #host = '{}:{}'.format(parsed_uri.hostname,parsed_uri.port)
        else:
            orig_path = '/'.join(request.url.path.split('/')[:-1])
            #host = cls._get_forwarded(request, 'host') or request.client.host


        path = "{}".format(path) if path is not None else request.url.path
        query = '?' + '&'.join(query_strings) if query_strings else ''
        jhost = host.split(':')
        url = '{}://{}:{}{}{}{}'.format(scheme, jhost[0],port, forwarded_path, path, query)
        return url

    @staticmethod
    def _get_forwarded(request, key):
        """Gets a forwarded value from the `Forwarded` header if present, or
        the equivalent `X-Forwarded-` header if not. If neither is present,
        returns an empty string.
        """
        forwarded = request.headers.get('Forwarded', '')
        match = re.search(
            r'(?<={}=).+?(?=[\s,;]|$)'.format(key),
            forwarded,
            re.IGNORECASE)

        if match is not None:
            header = match.group(0)

            if header[0] == '"' and header[-1] == '"':
                return header[1:-1]

            return header

        return request.headers.get('X-Forwarded-{}'.format(key.title()), '')

    @classmethod
    def _expand_block(cls, block):
        """Deserializes a Block's header, and the header of its Batches.
        """
        cls._parse_header(BlockHeader, block)
        if 'batches' in block:
            block['batches'] = [cls._expand_batch(b) for b in block['batches']]
        return block

    @classmethod
    def _expand_batch(cls, batch):
        """Deserializes a Batch's header, and the header of its Transactions.
        """
        cls._parse_header(BatchHeader, batch)
        if 'transactions' in batch:
            batch['transactions'] = [
                cls._expand_transaction(t) for t in batch['transactions']]
        return batch

    @classmethod
    def _expand_transaction(cls, transaction):
        """Deserializes a Transaction's header.
        """
        return cls._parse_header(TransactionHeader, transaction)

    @classmethod
    def _parse_header(cls, header_proto, resource):
        """Deserializes a resource's base64 encoded Protobuf header.
        """
        header = header_proto()
        try:
            header_bytes = base64.b64decode(resource['header'])
            header.ParseFromString(header_bytes)
        except (KeyError, TypeError, ValueError, DecodeError):
            header = resource.get('header', None)
            LOGGER.error(
                'The validator sent a resource with %s %s',
                'a missing header' if header is None else 'an invalid header:',
                header or '')
            raise errors.ResourceHeaderInvalid()

        resource['header'] = cls._message_to_dict(header)
        if 'consensus' in resource['header']:
            seal = resource['header']['consensus']
            LOGGER.debug(f'EXPAND CONSENSUS SEAL: {seal}')
        return resource

    @staticmethod
    def _get_paging_controls(request):
        """Parses start and/or limit queries into a paging controls dict.
        """
        start = request.query_params.get(FA_PAGE_START, None)
        limit = request.query_params.get(FA_PAGE_LIMIT, None)
        controls = {}

        if limit is not None:
            try:
                controls[PAGE_LIMIT] = int(limit)
            except ValueError:
                LOGGER.debug('Request query had an invalid limit: %s', limit)
                raise errors.CountInvalid()

            if controls[PAGE_LIMIT] <= 0:
                LOGGER.debug('Request query had an invalid limit: %s', limit)
                raise errors.CountInvalid()

        if start is not None:
            controls[PAGE_START] = start

        return controls

    @staticmethod
    def _make_paging_message(controls):
        """Turns a raw paging controls dict into Protobuf ClientPagingControls.
        """

        return client_list_control_pb2.ClientPagingControls(
            start=controls.get('start', None),
            limit=controls.get('limit', None))

    @staticmethod
    def _get_sorting_message(request, key):
        """Parses the reverse query into a list of ClientSortControls protobuf
        messages.
        """
        control_list = []
        reverse = request.query_params.get('reverse', None)
        if reverse is None:
            return control_list

        if reverse.lower() == "":
            control_list.append(client_list_control_pb2.ClientSortControls(
                reverse=True,
                keys=key.split(",")
            ))
        elif reverse.lower() != 'false':
            control_list.append(client_list_control_pb2.ClientSortControls(
                reverse=True,
                keys=reverse.split(",")
            ))

        return control_list

    def _set_wait(self, request, validator_query):
        """Parses the `wait` query parameter, and sets the corresponding
        `wait` and `timeout` properties in the validator query.
        """
        wait = request.query_params.get('wait', 'false')
        if wait.lower() != 'false':
            validator_query.wait = True
            try:
                validator_query.timeout = int(wait)
            except ValueError:
                # By default, waits for 95% of REST API's configured timeout
                validator_query.timeout = int(self._timeout * 0.95)

    def _drop_empty_props(self, item):
        """Remove properties with empty strings from nested dicts.
        """
        if isinstance(item, list):
            return [self._drop_empty_props(i) for i in item]
        if isinstance(item, dict):
            return {
                k: self._drop_empty_props(v)
                for k, v in item.items() if v != ''
            }
        return item

    def _drop_id_prefixes(self, item):
        """Rename keys ending in 'id', to just be 'id' for nested dicts.
        """
        if isinstance(item, list):
            return [self._drop_id_prefixes(i) for i in item]
        if isinstance(item, dict):
            return {
                'id' if k.endswith('id') else k: self._drop_id_prefixes(v)
                for k, v in item.items()
            }
        return item

    @classmethod
    def _get_head_id(cls, request):
        """Fetches the request's head query, and validates if present.
        """
        head_id = request.query_params.get('head', None)

        if head_id is not None:
            cls._validate_id(head_id)

        return head_id

    @classmethod
    def _get_filter_ids(cls, request):
        """Parses the `id` filter paramter from the url query.
        """
        id_query = request.query_params.get('id', None)

        if id_query is None:
            return None

        filter_ids = id_query.split(',')
        for filter_id in filter_ids:
            cls._validate_id(filter_id)

        return filter_ids

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
            LOGGER.debug('_head_to_root ask list block')                                              
                                                                                                      
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
    

    async def get_state_by_addr(self,address,root=''):
        error_traps = [error_handlers.InvalidAddressTrap,error_handlers.StateNotFoundTrap]  
                                                       
        response = await self._query_validator(                                                                                            
            Message.CLIENT_STATE_GET_REQUEST,                                                                                              
            client_state_pb2.ClientStateGetResponse,                                                                                       
            client_state_pb2.ClientStateGetRequest(state_root=root,address=address),                                                                                                          
            error_traps)

        return response 
    
    async def get_states_by_addr(self, request,address):                                                              
        """Fetches list of data entries, optionally filtered by address prefix.                       
                                                                                                      
        Request:                                                                                      
            query:                                                                                    
                - head: The id of the block to use as the head of the chain                           
                - address: Return entries whose addresses begin with this                             
                prefix                                                                                
                                                                                                      
        Response:                                                                                     
            data: An array of leaf objects with address and data keys                                 
            head: The head used for this query (most recent if unspecified)                           
            link: The link to this exact query, including head block                                  
            paging: Paging info and nav, like total resources and a next link                         
        """                                                                                           
        paging_controls = self._get_paging_controls(request)                                          
        # for DAG ask head of chain for getting merkle root is incorrect way                          
        # FIXME - add special method for asking real merkle root                                      
        #head, root = await self._head_to_root(request.query_params.get('head', None))                    
        #LOGGER.debug('LIST_STATE STATE=%s',root[:10])                                                 
        head = None                                                                                               
        validator_query = client_state_pb2.ClientStateListRequest(                                    
            state_root='',#root,                                                                      
            address=address, #request.url.query.get('address', None),                                           
            sorting=self._get_sorting_message(request, "default"),                                    
            paging=self._make_paging_message(paging_controls))                                        
                                                                                                      
        response = await self._query_validator(                                                       
            Message.CLIENT_STATE_LIST_REQUEST,                                                        
            client_state_pb2.ClientStateListResponse,                                                 
            validator_query)                                                                          
        return response                                                                                              
        return self._wrap_paginated_response(                                                         
            request=request,                                                                          
            response=response,                                                                        
            controls=paging_controls,                                                                 
            data=response.get('entries', []),                                                         
            head=head)                                                                                
    
         




if settings.OPENTSDB_ENABLE > 0:
    LOGGER.debug('Use OPENTSDB: %s',settings.OPENTSDB_URL)
    url = urlparse(settings.OPENTSDB_URL)                                       
    proto, db_server, db_port, = url.scheme, url.hostname, url.port                    
                                                                                       
    registry = MetricsRegistry()                                                       
    wrapped_registry = MetricsRegistryWrapper(registry)                                
                                                                                       
    reporter = InfluxReporter(                                                         
        registry=registry,                                                             
        reporting_interval=settings.REPORTING_INTERVAL,                                                         
        database=settings.OPENTSDB_DB,                                          
        prefix=settings.REPORTING_PREFIX,                                                         
        port=db_port,                                                                  
        protocol=proto,                                                                
        server=db_server,                                                              
        username=settings.OPENTSDB_UNAME,                                    
        password=settings.OPENTSDB_PASSW)                                    
    reporter.start()                                                                   





else:
    LOGGER.debug('Without  OPENTSDB')
    wrapped_registry = None

connection = Connection(settings.DGT_CONNECT)
query_validator = QueryValidatorHandler(connection,timeout=settings.DEFAULT_TIMEOUT,metrics_registry=wrapped_registry)

def getQueryValidator():
    return query_validator



