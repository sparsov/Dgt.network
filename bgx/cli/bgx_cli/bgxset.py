# Copyright 2020 DGT NETWORK INC 
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

import argparse
from base64 import b64decode
import csv
import getpass
import hashlib
import json
import logging
import os
import sys
import traceback
import random
import yaml
import time
import pkg_resources
from colorlog import ColoredFormatter

from bgx_cli.exceptions import CliException
from bgx_cli.rest_client import RestClient
from bgx_cli.make_set_txn import _create_batch,_create_propose_txn,_create_topology_txn,_create_vote_txn,_key_to_address


from bgx_cli.protobuf.settings_pb2 import SettingCandidates
#from bgx_cli.protobuf.setting_pb2 import Setting
from sawtooth_validator.protobuf.setting_pb2 import Setting

#from bgx_cli.protobuf.transaction_pb2 import TransactionHeader
#from bgx_cli.protobuf.transaction_pb2 import Transaction

from sawtooth_validator.protobuf.batch_pb2 import BatchList
#from bgx_cli.protobuf.batch_pb2 import BatchList

from sawtooth_signing import create_context
from sawtooth_signing import CryptoFactory
from sawtooth_signing import ParseError
from sawtooth_signing.secp256k1 import Secp256k1PrivateKey
from sawtooth_validator.gossip.fbft_topology import PeerSync,PeerRole,PeerAtr,FbftTopology,TOPOLOGY_SET_NM

DISTRIBUTION_NAME = 'bgxset'

_MIN_PRINT_WIDTH = 15

def setting_key_to_address(key):
    return _key_to_address(key)

def add_config_parser(subparsers, parent_parser):
    """Creates the arg parsers needed for the config command and
    its subcommands.
    """
    parser = subparsers.add_parser(
        'config',
        help='Changes genesis block settings and create, view, and '
        'vote on settings proposals',
        description='Provides subcommands to change genesis block settings '
                    'and to view, create, and vote on existing proposals.'
    )

    config_parsers = parser.add_subparsers(title="subcommands",
                                           dest="subcommand")
    config_parsers.required = True


def _do_config_proposal_create(args):
    """Executes the 'proposal create' subcommand.  Given a key file, and a
    series of key/value pairs, it generates batches of sawtooth_settings
    transactions in a BatchList instance.  The BatchList is either stored to a
    file or submitted to a validator, depending on the supplied CLI arguments.
    """
    settings = [s.split('=', 1) for s in args.setting]

    signer = _read_signer(args.key)

    txns = [_create_propose_txn(signer, setting)
            for setting in settings]

    batch = _create_batch(signer, txns)

    batch_list = BatchList(batches=[batch])

    if args.output is not None:
        try:
            with open(args.output, 'wb') as batch_file:
                batch_file.write(batch_list.SerializeToString())
        except IOError as e:
            raise CliException(
                'Unable to write to batch file: {}'.format(str(e)))
    elif args.url is not None:
        rest_client = RestClient(args.url)
        rest_client.send_batches(batch_list)
    else:
        raise AssertionError('No target for create set.')


def _do_config_proposal_list(args):
    """Executes the 'proposal list' subcommand.

    Given a url, optional filters on prefix and public key, this command lists
    the current pending proposals for settings changes.
    """

    def _accept(candidate, public_key, prefix):
        # Check to see if the first public key matches the given public key
        # (if it is not None).  This public key belongs to the user that
        # created it.
        has_pub_key = (not public_key
                       or candidate.votes[0].public_key == public_key)
        has_prefix = candidate.proposal.setting.startswith(prefix)
        return has_prefix and has_pub_key

    candidates_payload = _get_proposals(RestClient(args.url))
    candidates = [
        c for c in candidates_payload.candidates
        if _accept(c, args.public_key, args.filter)
    ]

    if args.format == 'default':
        for candidate in candidates:
            print('{}: {} => {}'.format(
                candidate.proposal_id,
                candidate.proposal.setting,
                candidate.proposal.value))
    elif args.format == 'csv':
        writer = csv.writer(sys.stdout, quoting=csv.QUOTE_ALL)
        writer.writerow(['PROPOSAL_ID', 'KEY', 'VALUE'])
        for candidate in candidates:
            writer.writerow([
                candidate.proposal_id,
                candidate.proposal.setting,
                candidate.proposal.value])
    elif args.format == 'json' or args.format == 'yaml':
        candidates_snapshot = \
            {c.proposal_id: {c.proposal.setting: c.proposal.value}
             for c in candidates}

        if args.format == 'json':
            print(json.dumps(candidates_snapshot, indent=2, sort_keys=True))
        else:
            print(yaml.dump(candidates_snapshot,
                            default_flow_style=False)[0:-1])
    else:
        raise AssertionError('Unknown format {}'.format(args.format))


def _do_config_proposal_vote(args):
    """Executes the 'proposal vote' subcommand.  Given a key file, a proposal
    id and a vote value, it generates a batch of bgx_settings transactions
    in a BatchList instance.  The BatchList is file or submitted to a
    validator.
    """
    signer = _read_signer(args.key)
    rest_client = RestClient(args.url)

    proposals = _get_proposals(rest_client)

    proposal = None
    for candidate in proposals.candidates:
        if candidate.proposal_id == args.proposal_id:
            proposal = candidate
            break

    if proposal is None:
        raise CliException('No proposal exists with the given id')

    for vote_record in proposal.votes:
        if vote_record.public_key == signer.get_public_key().as_hex():
            raise CliException(
                'A vote has already been recorded with this signing key')

    txn = _create_vote_txn(
        signer,
        args.proposal_id,
        proposal.proposal.setting,
        args.vote_value)
    batch = _create_batch(signer, [txn])

    batch_list = BatchList(batches=[batch])

    rest_client.send_batches(batch_list)


def _do_config_genesis(args):
    signer = _read_signer(args.key)
    public_key = signer.get_public_key().as_hex()

    authorized_keys = args.authorized_key if args.authorized_key else \
        [public_key]
    if public_key not in authorized_keys:
        authorized_keys.append(public_key)

    txns = []

    txns.append(_create_propose_txn(
        signer,
        ('sawtooth.settings.vote.authorized_keys',
         ','.join(authorized_keys))))

    if args.approval_threshold is not None:
        if args.approval_threshold < 1:
            raise CliException('approval threshold must not be less than 1')

        if args.approval_threshold > len(authorized_keys):
            raise CliException(
                'approval threshold must not be greater than the number of '
                'authorized keys')

        txns.append(_create_propose_txn(
            signer,
            ('sawtooth.settings.vote.approval_threshold',
             str(args.approval_threshold))))

    batch = _create_batch(signer, txns)
    batch_list = BatchList(batches=[batch])

    try:
        with open(args.output, 'wb') as batch_file:
            batch_file.write(batch_list.SerializeToString())
        print('Generated {}'.format(args.output))
    except IOError as e:
        raise CliException(
            'Unable to write to batch file: {}'.format(str(e)))


def _get_proposals(rest_client):
    state_leaf = rest_client.get_leaf(
        _key_to_address('sawtooth.settings.vote.proposals'))

    config_candidates = SettingCandidates()

    if state_leaf is not None:
        setting_bytes = b64decode(state_leaf['data'])
        setting = Setting()
        setting.ParseFromString(setting_bytes)

        candidates_bytes = None
        for entry in setting.entries:
            if entry.key == 'sawtooth.settings.vote.proposals':
                candidates_bytes = entry.value

        if candidates_bytes is not None:
            decoded = b64decode(candidates_bytes)
            config_candidates.ParseFromString(decoded)

    return config_candidates


def _read_signer(key_filename):
    """Reads the given file as a hex key.

    Args:
        key_filename: The filename where the key is stored. If None,
            defaults to the default key for the current user.

    Returns:
        Signer: the signer

    Raises:
        CliException: If unable to read the file.
    """
    filename = key_filename
    if filename is None:
        filename = os.path.join(os.path.expanduser('~'),
                                '.dgt',
                                'keys',
                                getpass.getuser() + '.priv')

    try:
        with open(filename, 'r') as key_file:
            signing_key = key_file.read().strip()
    except IOError as e:
        raise CliException('Unable to read key file: {}'.format(str(e)))

    try:
        private_key = Secp256k1PrivateKey.from_hex(signing_key)
    except ParseError as e:
        raise CliException('Unable to read key in file: {}'.format(str(e)))

    context = create_context('secp256k1')
    crypto_factory = CryptoFactory(context)
    return crypto_factory.new_signer(private_key)

def _get_topology(rest_client,args):
    """
    load topology
    """
    state_leaf = rest_client.get_leaf(_key_to_address(TOPOLOGY_SET_NM))

    #config_candidates = SettingCandidates()
    topology = None
    if state_leaf is not None:
        setting_bytes = b64decode(state_leaf['data'])
        setting = Setting()
        setting.ParseFromString(setting_bytes)
        for entry in setting.entries:
            if entry.key == TOPOLOGY_SET_NM:
                topology = json.loads(entry.value.replace("'",'"'))
                if args.cls is not None:
                    print('topology cluster',args.cls)
                    fbft = FbftTopology()
                    fbft.get_topology(topology,'','','static')
                    if args.peer is None:
                        topology = fbft.get_cluster_by_name(args.cls)
                        #print('cluster',topology)
                        """
                        for key,peer in fbft.get_cluster_iter(args.cls):
                            print('cluster',args.cls,'peer',peer)
                        """
                    else:
                        topology,_ = fbft.get_peer_by_name(args.cls,args.peer)
                    #print('CLUSTER',args.cls,args.peer,'>>>',cls)
                
        

    return topology

def _do_list_topology(args):
    """
     Executes the 'topology list' subcommand.  
    """
    #signer = _read_signer(args.key)
    rest_client = RestClient(args.url)

    topology = _get_topology(rest_client,args)

    if topology is None:
        raise CliException('No topology exists ')
    """
    for vote_record in proposal.votes:
        if vote_record.public_key == signer.get_public_key().as_hex():
            raise CliException(
                'A vote has already been recorded with this signing key')
    """
    
    print('topology ',args.cls,args.peer,'>>>',topology)
    """
    txn = _create_vote_txn(
        signer,
        args.proposal_id,
        proposal.proposal.setting,
        args.vote_value)
    batch = _create_batch(signer, [txn])

    batch_list = BatchList(batches=[batch])

    rest_client.send_batches(batch_list)
    """
def _param_show(rest_client,args):
    """
    show topology param
    """
    fname = ('' if args.param_name[:4] == "bgx." else "bgx.") + args.param_name
    try:
        state_leaf = rest_client.get_leaf(_key_to_address(fname))
    except CliException:
        print('undef param {}'.format(fname))
        return

    
    if state_leaf is not None:
        setting_bytes = b64decode(state_leaf['data'])
        setting = Setting()
        setting.ParseFromString(setting_bytes)
        for entry in setting.entries:
            if entry.key == fname:
                print('{} = {}'.format(fname,entry.value))
    else:
        print('undef param {}'.format(fname))

def _param_topology(rest_client,signer,args):
    """
    set topology params
    """
    #print('_param_topology args',args,'>>>')
    if args.new == '':
        # show value
        _param_show(rest_client,args)
    else:
        #set value
        fname = ('' if args.param_name[:4] == "bgx." else "bgx.") + args.param_name
        txns = [_create_propose_txn(signer, (fname,args.new))]
        batch = _create_batch(signer, txns)

        batch_list = BatchList(batches=[batch])

        if args.url is not None:
            rest_client = RestClient(args.url)
            rest_client.send_batches(batch_list)
        else:
            raise AssertionError('No target for create set.')

def _set_topology(rest_client,signer,args):
    """
    set topology
    """
    param = {}
    if args.cls:
        param['cluster'] = args.cls
    if args.peer:
        param['peer'] = args.peer
    if args.oper:
        param['oper'] = args.oper
    if args.oper:
        param['list'] = args.list
    if args.oper:
        param['pid'] = args.pid

    val = json.dumps(param, sort_keys=True, indent=4)
    print('topology val',val,'>>>')
    txns = [_create_topology_txn(signer, (TOPOLOGY_SET_NM,val))]

    batch = _create_batch(signer, txns)

    batch_list = BatchList(batches=[batch])

    if args.url is not None:
        rest_client = RestClient(args.url)
        rest_client.send_batches(batch_list)
    else:
        raise AssertionError('No target for create set.')

    

def _do_param_topology(args):
    """
     Executes the 'topology set' subcommand.  
    """
    signer = _read_signer(args.key)
    rest_client = RestClient(args.url)
    _param_topology(rest_client,signer,args)


def _do_set_topology(args):
    """
     Executes the 'topology set' subcommand.  
    """
    signer = _read_signer(args.key)
    rest_client = RestClient(args.url)

    _set_topology(rest_client,signer,args)

    print('topology SET',args.cls,args.peer,'>>>')


def create_console_handler(verbose_level):
    clog = logging.StreamHandler()
    formatter = ColoredFormatter(
        "%(log_color)s[%(asctime)s %(levelname)-8s%(module)s]%(reset)s "
        "%(white)s%(message)s",
        datefmt="%H:%M:%S",
        reset=True,
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red',
        })

    clog.setFormatter(formatter)

    if verbose_level == 0:
        clog.setLevel(logging.WARN)
    elif verbose_level == 1:
        clog.setLevel(logging.INFO)
    else:
        clog.setLevel(logging.DEBUG)

    return clog


def setup_loggers(verbose_level):
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(create_console_handler(verbose_level))


def create_parent_parser(prog_name):
    parent_parser = argparse.ArgumentParser(prog=prog_name, add_help=False)
    parent_parser.add_argument(
        '-v', '--verbose',
        action='count',
        help='enable more verbose output')

    try:
        version = pkg_resources.get_distribution(DISTRIBUTION_NAME).version
    except pkg_resources.DistributionNotFound:
        version = 'UNKNOWN'

    parent_parser.add_argument(
        '-V', '--version',
        action='version',
        version=(DISTRIBUTION_NAME + ' (Hyperledger Sawtooth-BGX) version {}')
        .format(version),
        help='display version information')

    return parent_parser


def create_parser(prog_name):
    parent_parser = create_parent_parser(prog_name)

    parser = argparse.ArgumentParser(
        description='Provides subcommands to change genesis block settings '
        'and to view, create, and vote on settings proposals.',
        parents=[parent_parser])

    subparsers = parser.add_subparsers(title='subcommands', dest='subcommand')
    subparsers.required = True

    # The following parser is for the `genesis` subcommand.
    # This command creates a batch that contains all of the initial
    # transactions for on-chain settings
    genesis_parser = subparsers.add_parser(
        'genesis',
        help='Creates a genesis batch file of settings transactions',
        description='Creates a Batch of settings proposals that can be '
                    'consumed by "bgxadm genesis" and used '
                    'during genesis block construction.'
    )
    genesis_parser.add_argument(
        '-k', '--key',
        type=str,
        help='specify signing key for resulting batches '
             'and initial authorized key')

    genesis_parser.add_argument(
        '-o', '--output',
        type=str,
        default='config-genesis.batch',
        help='specify the output file for the resulting batches')

    genesis_parser.add_argument(
        '-T', '--approval-threshold',
        type=int,
        help='set the number of votes required to enable a setting change')

    genesis_parser.add_argument(
        '-A', '--authorized-key',
        type=str,
        action='append',
        help='specify a public key for the user authorized to submit '
             'config transactions')

    # The following parser is for the `proposal` subcommand group. These
    # commands allow the user to create proposals which may be applied
    # immediately or placed in ballot mode, depending on the current on-chain
    # settings.

    proposal_parser = subparsers.add_parser(
        'proposal',
        help='Views, creates, or votes on settings change proposals',
        description='Provides subcommands to view, create, or vote on '
                    'proposed settings')
    proposal_parsers = proposal_parser.add_subparsers(
        title='subcommands',
        dest='proposal_cmd')
    proposal_parsers.required = True

    prop_parser = proposal_parsers.add_parser(
        'create',
        help='Creates proposals for setting changes',
        description='Create proposals for settings changes. The change '
                    'may be applied immediately or after a series of votes, '
                    'depending on the vote threshold setting.'
    )

    prop_parser.add_argument(
        '-k', '--key',
        type=str,
        help='specify a signing key for the resulting batches')

    prop_target_group = prop_parser.add_mutually_exclusive_group()
    prop_target_group.add_argument(
        '-o', '--output',
        type=str,
        help='specify the output file for the resulting batches')

    prop_target_group.add_argument(
        '--url',
        type=str,
        help="identify the URL of a validator's REST API",
        default='http://localhost:8008')

    prop_parser.add_argument(
        'setting',
        type=str,
        nargs='+',
        help='configuration setting as key/value pair with the '
        'format <key>=<value>')

    proposal_list_parser = proposal_parsers.add_parser(
        'list',
        help='Lists the currently proposed (not active) settings',
        description='Lists the currently proposed (not active) settings. '
                    'Use this list of proposals to find proposals to '
                    'vote on.')

    proposal_list_parser.add_argument(
        '--url',
        type=str,
        help="identify the URL of a validator's REST API",
        default='http://localhost:8008')

    proposal_list_parser.add_argument(
        '--public-key',
        type=str,
        default='',
        help='filter proposals from a particular public key')

    proposal_list_parser.add_argument(
        '--filter',
        type=str,
        default='',
        help='filter keys that begin with this value')

    proposal_list_parser.add_argument(
        '--format',
        default='default',
        choices=['default', 'csv', 'json', 'yaml'],
        help='choose the output format')

    vote_parser = proposal_parsers.add_parser(
        'vote',
        help='Votes for specific setting change proposals',
        description='Votes for a specific settings change proposal. Use '
                    '"bgxset proposal list" to find the proposal id.')

    vote_parser.add_argument(
        '--url',
        type=str,
        help="identify the URL of a validator's REST API",
        default='http://localhost:8008')

    vote_parser.add_argument(
        '-k', '--key',
        type=str,
        help='specify a signing key for the resulting transaction batch')

    vote_parser.add_argument(
        'proposal_id',
        type=str,
        help='identify the proposal to vote on')

    vote_parser.add_argument(
        'vote_value',
        type=str,
        choices=['accept', 'reject'],
        help='specify the value of the vote')

    # add parser for topology
    #
    topology_parser = subparsers.add_parser(
        'topology',
        help='Views, creates, or change node in topology',
        description='Provides subcommands to view, create, or change '
                    'topology settings')
    topology_parsers = topology_parser.add_subparsers(
        title='subcommands',
        dest='topology_cmd')
    topology_parsers.required = True
    topology_list_parser = topology_parsers.add_parser(
        'list',
        help='Lists current topology',
        description='Lists the current topology  settings. '
                    )
    topology_list_parser.add_argument(
        '-c', '--cls',
        type=str,
        help='specify cluster name')
    topology_list_parser.add_argument(
        '-p', '--peer',
        type=str,
        help='specify peer name')

    topology_list_parser.add_argument(
        '--url',
        type=str,
        help="identify the URL of a validator's REST API",
        default='http://localhost:8008')
    # SET 
    topology_set_parser = topology_parsers.add_parser(
        'set',
        help='change current topology',
        description='change the current topology  settings. '
                    )
    topology_set_parser.add_argument(
        '-c', '--cls',
        type=str,
        help='specify cluster name')
    topology_set_parser.add_argument(
        '-p', '--peer',
        type=str,
        help='specify peer name')
    topology_set_parser.add_argument(
        '-o', '--oper',
        type=str,
        help='specify peer attribute')
    topology_set_parser.add_argument(
        '-k', '--key',
        type=str,
        help='specify signing key for resulting batches and initial authorized key',
        default='clusters/c1/bgx1/keys/validator.priv'
        )
    topology_set_parser.add_argument(
        '-i', '--pid',
        type=str,
        help='specify key of peer instead of cluster+peer',
        )
    topology_set_parser.add_argument(
        '-l', '--list',
        type=str,
        help='Peers JSON description',
        )
    topology_set_parser.add_argument(
        '--url',
        type=str,
        help="identify the URL of a validator's REST API",
        default='http://localhost:8008')
    # PARAM
    topology_param_parser = topology_parsers.add_parser(
        'param',
        help='change topology settings',
        description='change topology  settings. '
                    )
    topology_param_parser.add_argument(
        '-k', '--key',
        type=str,
        help='specify signing key for resulting batches and initial authorized key',
        default='clusters/c1/bgx1/keys/validator.priv'
        )
    topology_param_parser.add_argument(
        '--url',
        type=str,
        help="identify the URL of a validator's REST API",
        default='http://bgx-api-c1-1:8008')
    topology_param_parser.add_argument(
        'param_name',
        type=str,
        help='identify the param')

    topology_param_parser.add_argument(
        '-n', '--new',
        default='',
        type=str,
        help='identify the value of param')

    return parser


def main(prog_name=os.path.basename(sys.argv[0]), args=None,
         with_loggers=True):
    parser = create_parser(prog_name)
    if args is None:
        args = sys.argv[1:]
    args = parser.parse_args(args)

    if with_loggers is True:
        if args.verbose is None:
            verbose_level = 0
        else:
            verbose_level = args.verbose
        setup_loggers(verbose_level=verbose_level)

    if args.subcommand == 'proposal' and args.proposal_cmd == 'create':
        _do_config_proposal_create(args)
    elif args.subcommand == 'proposal' and args.proposal_cmd == 'list':
        _do_config_proposal_list(args)
    elif args.subcommand == 'proposal' and args.proposal_cmd == 'vote':
        _do_config_proposal_vote(args)
    elif args.subcommand == 'genesis':
        _do_config_genesis(args)
    elif args.subcommand == 'topology':
        if args.topology_cmd == 'list':
            _do_list_topology(args)
        elif args.topology_cmd == 'set':
            _do_set_topology(args)
        elif args.topology_cmd == 'param':
            _do_param_topology(args)
        else:
            raise CliException('"{}" is not a valid subcommand of "topology"'.format(args.subcommand))
    #elif args.subcommand == 'fbft':

    else:
        raise CliException(
            '"{}" is not a valid subcommand of "config"'.format(
                args.subcommand))


def main_wrapper():
    # pylint: disable=bare-except
    try:
        main()
    except CliException as e:
        print("Error: {}".format(e), file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        pass
    except BrokenPipeError:
        sys.stderr.close()
    except SystemExit as e:
        raise e
    except:
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
