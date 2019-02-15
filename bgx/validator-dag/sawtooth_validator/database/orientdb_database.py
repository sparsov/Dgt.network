# Copyright 2018 NTRLab
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

import logging
import os
import lmdb
import struct

# Orientdb
import pyorient
from urllib.parse import urlparse

from sawtooth_validator.database import database


LOGGER = logging.getLogger(__name__)

DEFAULT_SIZE = 1024**4
#
ORIENTDB_HOST,DB_NAME = "orientdb-test", "sw"
DB_USER,DB_PASS = "admin","foo"
STORAGE_TYPE = pyorient.STORAGE_TYPE_MEMORY  # pyorient.STORAGE_TYPE_PLOCAL
CLUSTER_TYPE = pyorient.CLUSTER_TYPE_MEMORY  # pyorient.CLUSTER_TYPE_PHYSICAL
BLOCK_CLUSTER = "block"
BLOCK_CLS = "@Block"
BLOCK_CMD = ["CREATE CLASS Block","CREATE PROPERTY Block.id STRING","CREATE PROPERTY Block.data STRING"]
CREATE_PROP = "CREATE PROPERTY Block.{} {}"
class IndexOutOfSyncError(Exception):
    pass


class OrientDatabase(database.Database):
    """IndexedDatabase is an implementation of the
    sawtooth_validator.database.Database interface which uses LMDB for the
    underlying persistence.

    It must be provided with a serializer and a deserializer.
    """

    def __init__(self, filename, serializer, deserializer,
                 indexes=None,
                 flag=None,
                 _size=DEFAULT_SIZE):
        """Constructor for the IndexedDatabase class.

        Args:
            filename (str): The filename in that case Database name - <host>:<port>/<db name>.
            serializer (function): converts entries to bytes
            deserializer (function): restores items from bytes
            indexes (dict:(str,function):optional): dict of index names to key
                functions.  The key functions use the deserialized value and
                produce n index keys, that will reference the items primary
                key. Defaults to None
            flag (str:optional): a flag indicating the mode for opening the
                database.  Refer to the documentation for anydbm.open().
                Defaults to None.
        """
        super(OrientDatabase, self).__init__()
        url = urlparse(filename,allow_fragments=True)
        print("ORIENTDB url=%s",url)
        if indexes is None:
            indexes = {}
        create = bool(flag == 'c')
        client = pyorient.OrientDB(ORIENTDB_HOST, 2424)
        LOGGER.info("TESTING ORIENTDB client=%s",client)
        session_id = client.connect( DB_USER, DB_PASS )
        LOGGER.debug("_ORIENTDB_ client=%s session_id=%s",client,session_id)
        #db = client.db_create( DB_NAME, pyorient.DB_TYPE_GRAPH, pyorient.STORAGE_TYPE_PLOCAL )
        is_db = client.db_exists( DB_NAME, STORAGE_TYPE )
        print('db_exists orient',is_db)
        if is_db and (flag == 'n' or flag == 'c'):
            # recreate DB
            client.db_drop(DB_NAME)
            is_db = False
        if not is_db:
            self._main_db = client.db_create( DB_NAME, pyorient.DB_TYPE_GRAPH, STORAGE_TYPE )
            print('CREATE orient',self._main_db)
        self._main_db = client.db_open( DB_NAME, DB_USER, DB_PASS )
        print('PARAMS indexes',indexes,'values',indexes.values())
        self._indexes = {name: self._make_index_tuple(name, index_info) for name, index_info in indexes.items()}
        print('_indexes ITEMS',self._indexes.values())

        if not is_db:
            # create Block cluster
            self._cluster_id = client.data_cluster_add(BLOCK_CLUSTER,CLUSTER_TYPE)
            print('CREATE cluster_id',self._cluster_id)
            batch_cmds = [] #['begin']
            for command in BLOCK_CMD:
                batch_cmds.append(command)
            #batch_cmds.append('commit retry 100')
            for name, _,intkey in self._indexes.values():
                # add field for index
                batch_cmds.append(CREATE_PROP.format(name,"LONG" if intkey else "STRING")) # BINARY

            cmd = ';'.join(batch_cmds)
            try:
                print('TRY CREATE Block',cmd)
                results = client.batch(cmd)
                print('CREATE Block results',results)
            except Exception as ex:
                print('Cant CREATE PROP',cmd,ex)
    
        self._client = client
        self._serializer = serializer
        self._deserializer = deserializer

        """  
        self._lmdb = lmdb.Environment(
            path=filename,
            map_size=_size,
            map_async=True,
            writemap=True,
            readahead=False,
            subdir=False,
            create=create,
            max_dbs=len(indexes) + 1,
            lock=True)

        self._main_db = self._lmdb.open_db('main'.encode())
        """  
        
        

    def _make_index_tuple(self, name, index_info):
        if callable(index_info):
            key_fn = index_info
            integerkey = False
        elif isinstance(index_info, dict):
            key_fn = index_info['key_fn']
            integerkey = index_info['integerkey'] \
                if 'integerkey' in index_info else False
        else:
            raise ValueError('Index {} must be defined as a function or a dict'.format(name))

        print("NAME of index",'index_{}'.format(name).encode(),'key_fn',key_fn)
        return (name,key_fn,integerkey) #self._lmdb.open_db('index_{}'.format(name).encode(),integerkey=integerkey),
                

    # pylint: disable=no-value-for-parameter
    def __len__(self):
        cnt = self._client.data_cluster_count([self._cluster_id])
        print('__LEN__',cnt)
        return cnt 
        """ 
        with self._lmdb.begin(db=self._main_db) as txn:
            return txn.stat()['entries']
        """
    def count(self, index=None):
        if index is None:
            return len(self)

        if index is not None and index not in self._indexes:
            raise ValueError('Index {} does not exist'.format(index))
        print('COUNT',self._indexes[index][0])
        return self._client.data_cluster_count([self._cluster_id])
        """
        with self._lmdb.begin(db=self._indexes[index][0]) as txn:
            return txn.stat()['entries']
        """
    def _get_num_query(self,query):
        try:    
            data = self._client.query(query)
            return data[0].cnt
        except Exception as ex:
            print("_get_num_query",ex)
            return -1

    def contains_key(self, key, index=None):
        
        if index is not None and index not in self._indexes:
            print('INDEX does not exist',index,self._indexes)
            raise ValueError('Index {} does not exist'.format(index))

        if index:
            search_db = self._indexes[index][0]
            print('USE index',search_db,type(search_db))
            query = "SELECT count(*) as cnt FROM Block where %s='%s'" % (search_db,key)
        else:
            query = "SELECT count(*) as cnt FROM Block where id='%s'" % (key)
        
        print('contains QUERY=',query)
        try:    
            data = self._client.query(query)
            print("get key,data",key,data[0],type(data[0]),data[0].cnt > 0)
            return data[0].cnt > 0

        except Exception as ex:
            print("cant get ",key,ex)
        return False
        """
        with self._lmdb.begin(db=search_db) as txn:
            return txn.cursor().set_key(key.encode())
        """
            
    def get_multi(self, keys, index=None):
        if index is not None and index not in self._indexes:
            raise ValueError('Index {} does not exist'.format(index))
        result = []
        print('GET_MULTI',keys,'index',index)
        cursor = _OrientCursor(self._client,(self._cluster_id,index),self._deserializer) 
        for key in keys:
            try:    
                packed = cursor.get(key,index=index)
                if packed is not None:
                    rec = self._deserializer(packed)
                    if not index:
                        result.append((str(key),rec))
                    else:
                        rkey = rec[0]
                        result.append((str(rkey),rec)) 
            except :
                pass
        print('GET_MULTI=',result)
        return result
        """
        with self._lmdb.begin() as txn:
            result = []
            cursor = txn.cursor(self._main_db)
            index_cursor = None
            if index is not None:
                index_db = self._indexes[index][0]
                index_cursor = txn.cursor(index_db)

            for key in keys:
                read_key = key.encode()
                # If we're looking at an index, check the index first
                if index_cursor:
                    try:
                        read_key = index_cursor.get(read_key)
                    except lmdb.BadValsizeError:
                        raise KeyError("Invalid key: %s" % read_key)
                    if not read_key:
                        continue

                try:
                    packed = cursor.get(read_key)
                except lmdb.BadValsizeError:
                    raise KeyError("Invalid key: %s" % read_key)

                if packed is not None:
                    result.append((read_key.decode(),
                                   self._deserializer(packed)))
                elif index_cursor:
                    raise IndexOutOfSyncError(
                        'Index is out of sync for key {}'.format(key))

        return result
        """

    def cursor(self, index=None):
        """
        index is field for ordering 
        """
        if index is not None and index not in self._indexes:
            raise ValueError('Index {} does not exist'.format(index))

        #db_chain = []
        #fetch_plan = "#{}:1".format(self._cluster_id) 
        #db_chain.append(self._cluster_id)
        """
        if index:
            db_chain.append(self._indexes[index][0])
        """
        #db_chain.append(self._main_db)
        return ReferenceChainCursor(self._client, (self._cluster_id,index), self._deserializer)

    def update(self, puts, deletes):
        """Applies the given puts and deletes atomically.
        Args:
            puts (:iterable:`tuple`): an iterable of key/value pairs to insert
            deletes (:iterable:str:) an iterable of keys to delete
        """
        # Process deletes first, to handle the case of new items replacing
        # Drop items
        for key in deletes:
            try:
                query = "DELETE FROM Block WHERE id = {}".format(key)
                print('DELETE',key,'QUERY',query)
                self._client.command(query)
            except Exception as ex:
                print('Cant DELETE',key,ex)
            #client.record_delete(<cluster-id>, <record-id>)
            """
            if not cursor.set_key(key.encode()):
                # value doesn't exist
                continue

            value = self._deserializer(bytes(cursor.value()))
            cursor.delete()
            # drop from index
            for (index_db, index_key_fn) in self._indexes.values():
                index_keys = index_key_fn(value)
                index_cursor = txn.cursor(index_db)
                for idx_key in index_keys:
                    if index_cursor.set_key(idx_key):
                        index_cursor.delete()
            """


        for key, value in puts:
            packed = self._serializer(value)
            #print('key,val',key,packed)
            event = {
                BLOCK_CLS: {
                    "id": key,
                    "data": packed.decode("utf-8"),
                },
            }
            # add index fields
            for (index_db, index_key_fn,intkey) in self._indexes.values():
                index_keys = index_key_fn(value)
                kval = index_keys[0].decode("utf-8")
                event[BLOCK_CLS][index_db] = struct.unpack('I', index_keys[0])[0] if intkey else kval
                print('index_keys IVAL',type(index_keys[0]),index_keys[0],'index_db',index_db)
                if intkey:
                    print('index_keys',struct.unpack('I', index_keys[0])[0])
            try:
                print('ADD record',event)
                self._client.record_create(self._cluster_id, event)
            except Exception as ex:
                print('cant add record',key,ex)

        return 
        """
        with self._lmdb.begin(write=True, buffers=True) as txn:
            cursor = txn.cursor(self._main_db)
            # Process deletes first, to handle the case of new items replacing
            # old index locations
            for key in deletes:
                if not cursor.set_key(key.encode()):
                    # value doesn't exist
                    continue

                value = self._deserializer(bytes(cursor.value()))
                cursor.delete()

                for (index_db, index_key_fn) in self._indexes.values():
                    index_keys = index_key_fn(value)
                    index_cursor = txn.cursor(index_db)
                    for idx_key in index_keys:
                        if index_cursor.set_key(idx_key):
                            index_cursor.delete()

            # process all the inserts
            for key, value in puts:
                packed = self._serializer(value)

                cursor.put(key.encode(), packed, overwrite=True)

                for (index_db, index_key_fn) in self._indexes.values():
                    index_keys = index_key_fn(value)
                    index_cursor = txn.cursor(index_db)
                    for idx_key in index_keys:
                        index_cursor.put(idx_key, key.encode())

        self.sync()
        """
    def sync(self):
        """Ensures that pending writes are flushed to disk
        """
        pass
        """
        self._lmdb.sync()
        """

    def close(self):
        """Closes the connection to the database
        """
        pass
        print("CLOSE ORIENT")
        """
        self._lmdb.close()
        """
    def keys(self, index=None):
        """Returns a list of keys in the database
        """
        if index is not None and index not in self._indexes:
            raise ValueError('Index {} does not exist'.format(index))

        db_fld = self._indexes[index][0] if index else 'id'
        num = self._get_num_query("select count(*) as cnt from Block") #  order by {}
        print('KEYS NUM',num)
        query = "select {} as val from Block order by {}".format(db_fld,db_fld)
        keys = []
        records = self._client.query(query,num)
        for rec in records:
            try:
                val = rec.oRecordData['val']
                keys.append(val)
            except:
                print('oRecordData undef VAl',rec.oRecordData)
        print('LEN',len(records),'QUERY',query,'KEYS',keys)
        return keys
        """
        with self._lmdb.begin(db=db) as txn:
            return [
                key.decode()
                for key in txn.cursor().iternext(keys=True, values=False)
            ]
        """

class _OrientCursor:
    def __init__(self,client,db,deserializer):
        self._cluster_id = db[0] #cluster_id
        self._index = db[1]
        self._client = client
        self._deserializer = deserializer
        self._curr = None
        self._value = None
        self._key = None
        self._dir  = 0

    def __iter__(self):
        return self

    def __next__(self):
        curr = self._curr
        print('_OrientCursor._next',curr,'+',self._dir,type(self._curr),type(self._dir))
        self._curr += self._dir
        
        return curr

    def key(self):
        return self._key if self._key else ''

    def iternext(self,keys=True,values=True):
        self._dir = 1
        if not self._curr:
            self._curr,self._key = 1, 1 
        else:
            self._curr = int(self._key)

        print('_OrientCursor.iternext',self._curr,keys)
        return self

    def iterprev(self,keys=True,values=True):
        self._dir = -1
        if not self._curr:
            self._curr = self._client.data_cluster_count([self._cluster_id]) 
            self._key  = self._curr
        else:
            self._curr = self._key

        print('_OrientCursor.iterprev',self._curr,keys)
        return self

    def first(self):
        self._curr,self._key = 1, 1

    def last(self):
        self._curr = self._client.data_cluster_count([self._cluster_id]) 
        self._key  = self._curr

    def get(self,key, default=None,index=None):
        if not index and not self._index:
            rkey = "#{}:{}".format(self._cluster_id,int(key)-1)
            packed = self._client.record_load(rkey)
            rec = packed.oRecordData
            if len(rec) == 0:
                self._curr = None
                raise IndexOutOfSyncError()
            packed = rec['data'].encode("utf-8")
            self._key = int(key)
            self._value = self._deserializer(packed)
            print('_OrientCursor.GET',rkey,'->',packed)
            return packed
        # use index 
        if index:
            query = "SELECT FROM Block where %s='%s'" % (index,key)
        else: # where id = {}
            skip = key-1 
            if skip < 0 :
                self._curr = None
                raise IndexOutOfSyncError()
            query = "SELECT FROM Block order by {} SKIP {} LIMIT 1".format(self._index,skip)
        print('QUERY=',query)
        packed = self._client.query(query)
        print('PACKED=',packed)
        if len(packed) == 0:
            self._curr = None
            raise IndexOutOfSyncError()
        rec = packed[0].oRecordData
        packed = rec['data'].encode("utf-8")
        self._value = self._deserializer(packed)
        self._key = key
        print('get:use index',index,self._key,self._value,type(self._curr)) 
        return packed

    def value(self):
        #Return the current value for self._key
        return self._value # read it 

    def set_key(self,key):
        print('_OrientCursor.set_key',key,key.decode())
        self._curr = int(key)
        try:
            self.get(key.decode(),index='id')
            return True
        except:
            return False

class ReferenceChainCursor(database.Cursor):
    """Cursor implementation that follows a chain of databases, where
    reference_chain is key_1 -> key_2 mappings with the final entry in the
    chain being key_n -> value.
    """

    def __init__(self, client, db, deserializer):
        self._client = client
        self._deserializer = deserializer
        self._lmdb_txn = None
        """
        if not reference_chain:
            raise ValueError("Must be at least one lmdb database in the reference chain")
        """
        self._db = db
        #self._lmdb_cursors = []

    def open(self):
        self._cluster_id = self._db[0]
        print('ReferenceChainCursor OPEN',self._db)
        #self._lmdb_cursors = [self._reference_chain[0]]
        self._curs = _OrientCursor(self._client,self._db,self._deserializer)
        print('OPEN',self._curs)

        """
        self._lmdb_txn = self._lmdb_env.begin()

        self._lmdb_cursors = [self._lmdb_txn.cursor(db)
                              for db in self._reference_chain]
        """

    def close(self):
        print('ReferenceChainCursor CLOSE')
        """
        for curs in self._lmdb_cursors:
            curs.close()

        self._lmdb_cursors = []
        # Event though this is a read-only txn, abort it, just to be sure
        self._lmdb_txn.abort()
        """

    def iter(self):
        print('CURS.ITER')
        return ReferenceChainCursor._wrap_iterator(self._curs.iternext(keys=False),self._deserializer)

    def iter_rev(self):
        print('CURS.ITER_REV')
        return ReferenceChainCursor._wrap_iterator(self._curs.iterprev(keys=False),self._deserializer)

    def first(self):
        return self._curs.first() 
        

    def last(self):
        return self._curs.last()

    def seek(self, key):
        print('SEEK',key)
        return self._curs.set_key(key.encode())

    def key(self):
        key = self._curs.key()
        return key
        """
        if key is not None:
            return key.decode()
        return None
        """

    def value(self):
        value = self._curs.value()
        if not value:
            return None
        return value
        """
        return _read(
            value,
            self._curs,
            self._deserializer)
        """

    @staticmethod
    def _wrap_iterator(iterator, deserializer):
        class _WrapperIter:
            def __iter__(self):
                #print('_WRAP_ITERATOR.__iter__')
                return self

            def __next__(self):
                #print('_WRAP_ITERATOR.__next__')
                try:
                    return _read(
                        next(iterator),
                        iterator,
                        deserializer)
                except IndexOutOfSyncError : #lmdb.Error:
                    raise StopIteration()

        return _WrapperIter()


def _read(initial_key,cursor, deserializer):
    key = initial_key
    packed = key
    #print('_READ',key)
    packed = cursor.get(key)
    
    """
    for curs in cursor_chain:
        packed = curs.get(key)
        if not packed:
            raise IndexOutOfSyncError('Index is out of date for key {}'.format(key))
        key = packed
    """
    return  deserializer(packed) #(3, "bob", "Bob's data") #
