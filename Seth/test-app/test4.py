from eth_keys import keys

from eth_utils import decode_hex,to_bytes,to_wei

from eth_typing import Address

from eth import constants

from eth.chains.base import MiningChain

from eth.consensus.pow import mine_pow_nonce

from eth.vm.forks.byzantium import ByzantiumVM

from eth.db.atomic import AtomicDB,MemoryDB
from eth.vm.forks.frontier import FrontierVM
from eth.chains.base import Chain
from eth.chains.base import MiningChain
from eth.consensus.pow import PowConsensus

db = AtomicDB() #MemoryDB()
#vm = FrontierVM(constants.GENESIS_BLOCK_NUMBER, db)
#chain = Chain(vm)
sender_private_key = keys.PrivateKey(to_bytes(hexstr='0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8'))
sender_address = sender_private_key.public_key.to_canonical_address()


SOME_ADDRESS = b'\x85\x82\xa2\x89V\xb9%\x93M\x03\xdd\xb4Xu\xe1\x8e\x85\x93\x12\xc1'

GENESIS_STATE = {

    SOME_ADDRESS: {

        "balance": to_wei(100000, 'ether'),

        "nonce": 0,

        "code": b'',

        "storage": {}

    },
    sender_address: {

        "balance": to_wei(100000, 'ether'),

        "nonce": 0,

        "code": b'',

        "storage": {}

    }

}



GENESIS_PARAMS = {
      'difficulty': 1,
      'gas_limit': 3141592,
      'timestamp': 1514764800,
  }
consensus = PowConsensus(constants.GENESIS_DIFFICULTY)


chain = MiningChain.configure(
    __name__='MyChain',
    
    vm_configuration=((constants.GENESIS_BLOCK_NUMBER, FrontierVM),),
    #consensus_context=consensus,
    chain_id=1,
).from_genesis(db,GENESIS_PARAMS,GENESIS_STATE)
genesis = chain.get_canonical_block_header_by_number(0)
print('genesis',genesis)
vm = chain.get_vm()
changes = vm.state
# before transaction
bal = changes.get_balance(SOME_ADDRESS)
print('SOME bal',bal)

sender_private_key = keys.PrivateKey(to_bytes(hexstr='0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8'))
sender_address = sender_private_key.public_key.to_canonical_address()

contract_address = to_bytes(hexstr='0x742d35Cc6634C0532925a3b844Bc454e4438f44e')
transaction = chain.create_unsigned_transaction(
    nonce=vm.state.get_nonce(sender_address),
    gas_price=0,#vm.state.get_gas_price(),
    gas=21000,  # Здесь можно указать другое значение газа
    to=SOME_ADDRESS,#b'\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\x02',
    value=to_wei(1, 'ether'),  # Здесь можно указать другое количество ETH
    data=b'',
    #v=chain.network_id,
    #r=0,
    #s=0,
)
signed_tx = transaction.as_signed_transaction(sender_private_key)
chain.apply_transaction(signed_tx)
block_result = vm.finalize_block(chain.get_block())
block = block_result.block
print('block',block)


balance = changes.get_balance(sender_address) 
print("balance ",balance,sender_address)
bal = changes.get_balance(SOME_ADDRESS)
print('SOME bal',bal)

