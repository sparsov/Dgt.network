from eth_keys import keys

from eth_utils import decode_hex,to_bytes,to_wei,function_abi_to_4byte_selector
from eth_abi import encode as  encode_abi
from eth_typing import Address

from eth import constants

from eth.chains.base import MiningChain

from eth.consensus.pow import mine_pow_nonce

from eth.vm.forks.byzantium import ByzantiumVM

from eth.db.atomic import AtomicDB,MemoryDB
from eth.vm.forks.frontier import FrontierVM
from eth.vm.forks.frontier.blocks import FrontierBlock
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

        "balance": to_wei(5000000, 'ether'),

        "nonce": 0,

        "code": b'',

        "storage": {}

    },
    sender_address: {

        "balance": int(5000000 * (10 ** 18)) ,#to_wei(10000000, 'ether'),

        "nonce": 0,

        "code": b'',

        "storage": {}

    }

}



GENESIS_PARAMS = {
      'difficulty': 1,
      'gas_limit': 3141592000000,
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
bal,bal1 = changes.get_balance(SOME_ADDRESS),changes.get_balance(sender_address)
print('SOME bal',bal,'\nSOME bal',bal1)

sender_private_key = keys.PrivateKey(to_bytes(hexstr='0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8'))
sender_address = sender_private_key.public_key.to_canonical_address()

contract_address = to_bytes(hexstr='0x742d35Cc6634C0532925a3b844Bc454e4438f44e')
transaction = chain.create_unsigned_transaction(
    nonce=vm.state.get_nonce(sender_address),
    gas_price=2,#vm.state.get_gas_price(),
    gas=21000,  # Здесь можно указать другое значение газа
    to=SOME_ADDRESS,#b'\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\x02',
    value=to_wei(1, 'ether'),  # Здесь можно указать другое количество ETH
    data=b'',
    #v=chain.network_id,
    #r=0,
    #s=0,
)
#contract_bytecode = "0x606060405260648060106000396000f3606060405260e060020a6000350463c6888fa181146027578063d09de08a14603b575b600080fd5b603a602a60003504636d4ce63c8114605b578063f2fde38b14606d575b600080fd5b604160415060028a8560405183529190600a90825261000f91600491909101906100d6565b604051809103906000f080158015610079573d6000803e3d6000fd5b506001600160a01b0381351690602001356100a6565b60408051808201825260156100d191600483018190525060409001905080808501906020018083838290600060046020846101000a81548173ffffffffffffffffffffffffffffffffffffffff021916908373ffffffffffffffffffffffffffffffffffffffff16021790555050565b60408051808201825260156101c391600483018190525060409001905080808501906020018083838290600060046020846101000a81548173ffffffffffffffffffffffffffffffffffffffff021916908373ffffffffffffffffffffffffffffffffffffffff16021790555050565b6000805490509056fea165627a7a72305820d5c99d6e85ff2ec6093ca010ea5c14380b2a69f0ee81683aa325295ec3bdc740029"
contract_address = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"  # Address for your contract
with open('./SimpleStorage.bin', 'rb') as f:
    contract_bytecode = f.read()

# Create a new transaction to deploy the contract
# Создать объект транзакции
gas_price = 1  # Укажите желаемую цену газа
gas_limit = 73921+2454+22514+2402  # Укажите желаемый лимит газа

transaction1 = chain.create_unsigned_transaction(
    nonce=1,#vm.state.get_nonce(sender_address),
    gas_price=gas_price,#1,#vm.state.get_gas_price(),
    gas=gas_limit,#21000,  # Здесь можно указать другое значение газа
    to = b'\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\x00',  # В этом случае контракт будет развернут, поэтому адрес None
    value=0,#to_wei(0.5, 'ether'),
    data = contract_bytecode,
)
signed_tx = transaction.as_signed_transaction(sender_private_key)

chain.apply_transaction(signed_tx)
if False:
    block = FrontierBlock(vm.state)

    # Имитируем выполнение транзакции в контексте блока
    transaction_context = BaseTransactionContext(
        gas_price=transaction.gas_price,
        origin=sender,
        gas_limit=transaction.gas,
        block=block,
    )





if True:
    function_set_abi = [{"inputs":[{"internalType":"uint256","name":"x","type":"uint256"}],"name":"set","outputs":[],"stateMutability":"nonpayable","type":"function"}]
    f_get_abi = [{"inputs":[],"name":"get","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]
    args = []
    selector = encode_abi(['uint256'], [12345])#encode_abi(['function'], [function_set_abi]).hex()[:10]
    print('selector',selector)
    method_signature = ['get()'.encode()]
    method_arguments = [            ]
    selector = encode_abi(['bytes'], ['get()'.encode()])
    print('selector',selector)

    signed_tx1 = transaction1.as_signed_transaction(sender_private_key)
    computation = chain.apply_transaction(signed_tx1)
    msg= computation[2].msg
    addr_contr = msg.storage_address
    print('computation {} msg={} addr={} caddr={}'.format(computation,msg,msg.storage_address,msg.code_address))
    print('computation GAS_USED={} REMAIN={} PRECOMP={}'.format(computation[1].gas_used,computation[2].get_gas_remaining(), computation[2].get_precompiles()))
    print('computation RAW ENTRIES={}   OUT={} IS={} RET={} CODE={}'.format(computation[2].get_raw_log_entries(),computation[2].output,computation[2].is_success,
                                                                            computation[2].return_data,computation[2].code
                                                                             ))
    transaction2 = chain.create_unsigned_transaction(
    nonce=2,#vm.state.get_nonce(sender_address),
    gas_price=1,#1,#vm.state.get_gas_price(),
    gas=100000,#21000,  # Здесь можно указать другое значение газа
    to = addr_contr,  # В этом случае контракт будет развернут, поэтому адрес None
    value=0,#to_wei(0.5, 'ether'),
    data = selector,
    )
    signed_tx2 = transaction2.as_signed_transaction(sender_private_key)
    computation2 = chain.apply_transaction(signed_tx2)
    msg= computation2[2].msg
    addr_contr = msg.storage_address
    print('computation2 {} msg={} addr={} caddr={} stv={} val={} data={} ISC={}'.format(computation2,msg,msg.storage_address,
                                                                  msg.code_address,msg.should_transfer_value,msg.value,msg.data,
                                                                  msg.is_create
                                                                  ))
    print('computation2 GAS_USED={} REMAIN={} PRECOMP={}'.format(computation2[1].gas_used,computation2[2].get_gas_remaining(),
                                                                 computation2[2].get_precompiles()))
    print('computation2 RAW ENTRIES={}   OUT={} IS={} RET={} CODE={}'.format(computation2[2].get_raw_log_entries(),
                                                                            computation2[2].output,computation[2].is_success,
                                                                            computation2[2].return_data,computation2[2].code
                                                                             ))




    #function_selector = function_abi_to_4byte_selector('set()')
    #while not computation.is_success:
    #    computation = state.mine_block()
    #contract_address = computation.contract_address
# Выполняем транзакцию
#with vm.state(read_only=False) as state_db:
#    computation = vm.apply_transaction(state_db, signed_tx1)



#

block_result = vm.finalize_block(chain.get_block())
block = block_result.block
print('block',block)


balance = vm.state.get_balance(sender_address) 
print("balance ",balance,sender_address)
bal = changes.get_balance(SOME_ADDRESS)
print('SOME bal',bal)

