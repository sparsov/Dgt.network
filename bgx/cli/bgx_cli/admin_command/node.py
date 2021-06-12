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

import os
import shutil
import sys

from bgx_cli.exceptions import CliException
from bgx_cli.admin_command.config import get_key_dir
from sawtooth_signing import create_context


def add_node_parser(subparsers, parent_parser):
    """Adds subparser command and flags for 'keygen' command.

    Args:
        subparsers (:obj:`ArguementParser`): The subcommand parsers.
        parent_parser (:obj:`ArguementParser`): The parent of the subcomman
            parsers.
    """
    description = 'Generates dirs for the peer'

    epilog = (
        'The dirs are stored in '
        '/project/peer/ and '
        
    )

    parser = subparsers.add_parser(
        'node',
        help=description,
        description=description + '.',
        epilog=epilog,
        parents=[parent_parser])

    
    parser.add_argument(
        'cluster_name',
        help='name of the cluster',
        nargs='?')
    parser.add_argument(
        'peer_name',
        help='name of the peer',
        nargs='?')
    parser.add_argument(
        '--force',
        help="overwrite files if they exist",
        action='store_true')

    parser.add_argument(
        '-q',
        '--quiet',
        help="do not display output",
        action='store_true')


def do_node(args):
    """Executes the dirs generation operation

    Args:
        args (:obj:`Namespace`): The parsed args.
    """
    def make_dir(dname):
        
        if os.path.exists(dname):                                              
            print('Dir exists: {}'.format(dname), file=sys.stderr) 
            if args.force:
                print('Recreate : {}'.format(dname), file=sys.stderr)
                os.rmdir(dname)
            else:
                return
        print('Create Dir : {}'.format(dname), file=sys.stderr)            
        os.mkdir(dname, mode=0o777)

    def copy_file(src,dst):
        try:
            if not os.path.isfile(dst) or args.force:
                shutil.copyfile(src, dst)
                shutil.copymode(src, dst)
                print('Copy file: {}'.format(dst), file=sys.stdout)
        except Exception as ex:
            print('Cant copy file: {} ({})'.format(dst,ex), file=sys.stdout)

    if args.cluster_name is not None:
        cluster_name = args.cluster_name
    else:
        cluster_name = 'dyn'
    if args.peer_name is not None:
        peer_name = args.peer_name
    else:
        peer_name = 'bgx1'

    node_dir = '/project/peer'
    etc_dyn_dir  = '/project/bgx/bgx/etc'
    if cluster_name == 'dyn':
        etc_dir  = '/project/bgx/bgx/etc' # config sources
    else:
        etc_dir = os.path.join("/project/bgx/clusters",cluster_name,peer_name,"etc")
        keys_dir = os.path.join("/project/bgx/clusters",cluster_name,peer_name,"keys")

    if not os.path.exists(node_dir):
        raise CliException("Peer directory does not exist: {}".format(node_dir))
    
    
    try:
        
        for filename in ["data", "etc","keys","logs","policy"]:                    
            dname = os.path.join(node_dir, filename) 
            make_dir(dname)                              
             
            if filename == 'etc':
                # add config
                for fnm in ["validator.toml", "log_config.toml","dgt.conf"]:
                    dst = os.path.join(dname, fnm)
                    if fnm == "log_config.toml":
                        src = os.path.join(etc_dyn_dir, fnm+".dyn")
                    elif fnm == "dgt.conf":
                        src = os.path.join(etc_dyn_dir, fnm+(".dyn" if cluster_name == 'dyn' else '.static'))
                    else:
                        src = os.path.join(etc_dir, fnm+(".dyn" if cluster_name == 'dyn' else ''))
                    copy_file(src,dst)

            elif filename == 'keys' and cluster_name != 'dyn':
                for fnm in ["validator.priv", "validator.pub"]:
                    dst = os.path.join(dname, fnm)
                    src = os.path.join(keys_dir, fnm)
                    copy_file(src,dst)

    except IOError as ioe:
        raise CliException('IOError: {}'.format(str(ioe)))
    except Exception as ex:
        raise CliException('Exception: {}'.format(str(ex)))
    
