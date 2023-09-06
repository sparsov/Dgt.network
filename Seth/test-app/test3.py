from eth_keys import keys

from eth_utils import decode_hex

from eth_typing import Address

from eth import constants

from eth.chains.base import MiningChain

from eth.consensus.pow import mine_pow_nonce

from eth.vm.forks.byzantium import ByzantiumVM

from eth.db.atomic import AtomicDB


GENESIS_PARAMS = {

    'difficulty': 1,

    'gas_limit': 3141592,

    # We set the timestamp, just to make this documented example reproducible.

    # In common usage, we remove the field to let py-evm choose a reasonable default.

    'timestamp': 1514764800,

}

SENDER_PRIVATE_KEY = keys.PrivateKey(

    decode_hex('0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8')

)

SENDER = Address(SENDER_PRIVATE_KEY.public_key.to_canonical_address())

RECEIVER = Address(b'\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\x02')
klass = MiningChain.configure(

    __name__='TestChain',

    vm_configuration=(

        (constants.GENESIS_BLOCK_NUMBER, ByzantiumVM),

    ))

chain = klass.from_genesis(AtomicDB(), GENESIS_PARAMS)

genesis = chain.get_canonical_block_header_by_number(0)

vm = chain.get_vm()

nonce = vm.state.get_nonce(SENDER)

tx = vm.create_unsigned_transaction(

    nonce=nonce,

    gas_price=0,

    gas=100000,

    to=RECEIVER,

    value=0,

    data=b'',

)
gas_limit = 2000000
gas_price = 0 #1
nonce = 0  # Указать правильный nonce


contract_bytecode = "0x606060405260648060106000396000f3606060405260e060020a6000350463c6888fa181146027578063d09de08a14603b575b600080fd5b603a602a60003504636d4ce63c8114605b578063f2fde38b14606d575b600080fd5b604160415060028a8560405183529190600a90825261000f91600491909101906100d6565b604051809103906000f080158015610079573d6000803e3d6000fd5b506001600160a01b0381351690602001356100a6565b60408051808201825260156100d191600483018190525060409001905080808501906020018083838290600060046020846101000a81548173ffffffffffffffffffffffffffffffffffffffff021916908373ffffffffffffffffffffffffffffffffffffffff16021790555050565b60408051808201825260156101c391600483018190525060409001905080808501906020018083838290600060046020846101000a81548173ffffffffffffffffffffffffffffffffffffffff021916908373ffffffffffffffffffffffffffffffffffffffff16021790555050565b6000805490509056fea165627a7a72305820d5c99d6e85ff2ec6093ca010ea5c14380b2a69f0ee81683aa325295ec3bdc740029"
contract_address = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"  # Address for your contract
sender_address = "0x90F8bf6A479f320ead074411a4B0e7944Ea8c9C1"  # Address of the sender

# Create a new transaction to deploy the contract
# Создать объект транзакции
tx = vm.create_unsigned_transaction(

    nonce=nonce,

    gas_price=gas_price,

    gas=gas_limit,

    to=RECEIVER,

    value=0,

    data=bytes(contract_bytecode,'utf-8'),

)

signed_tx = tx.as_signed_transaction(SENDER_PRIVATE_KEY)

chain.apply_transaction(signed_tx)
#(<ByzantiumBlock(#Block #1...)

# Normally, we can let the timestamp be chosen automatically, but

# for the sake of reproducing exactly the same block every time,

# we will set it manually here:

chain.set_header_timestamp(genesis.timestamp + 1)

# We have to finalize the block first in order to be able read the

# attributes that are important for the PoW algorithm

block_result = chain.get_vm().finalize_block(chain.get_block())

block = block_result.block
# based on mining_hash, block number and difficulty we can perform

# the actual Proof of Work (PoW) mechanism to mine the correct

# nonce and mix_hash for this block
print('BLOCK',block)
nonce, mix_hash = mine_pow_nonce(

    block.number,

    block.header.mining_hash,

    block.header.difficulty,

)  

chain.mine_block(mix_hash=mix_hash, nonce=nonce)
