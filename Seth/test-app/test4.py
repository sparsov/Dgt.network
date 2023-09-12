from eth_keys import keys

from eth_utils import decode_hex,to_bytes,to_wei,function_abi_to_4byte_selector
from eth_abi import encode as  encode_abi
from eth_typing import Address

from eth import constants

from eth.chains.base import MiningChain
from eth.chains.ropsten import RopstenChain
from eth.consensus.pow import mine_pow_nonce

from eth.vm.forks.byzantium import ByzantiumVM

from eth.db.atomic import AtomicDB,MemoryDB
from eth.vm.forks.frontier import FrontierVM
from eth.vm.forks.frontier.blocks import FrontierBlock
from eth.chains.base import Chain
from eth.chains.base import MiningChain
from eth.consensus.pow import PowConsensus
import binascii

def check_computation(computation,title="computation"):
    msg= computation[2].msg   
    receipt  = computation[1]                                                                                                   
    addr_contr = msg.storage_address                                                                                                  
    print('{}:: {} msg={} addr={} caddr={} stv={} val={} data={} ISC={}'.format(title,computation,msg,msg.storage_address,         
                                                                  msg.code_address,msg.should_transfer_value,msg.value,msg.data,      
                                                                  msg.is_create                                                       
                                                                  )) 
    try:
        print('{}:: GAS_USED={} REMAIN={} PRECOMP={}'.format(title,receipt.gas_used,computation[2].get_gas_remaining(),        
                                                                     computation[2].get_precompiles())) 
    except Exception as ex:
        print('{}:: err {}'.format(title,ex))
    try:
        print('{}:: RAW ENTRIES={}   OUT={} IS={} RET={} CODE={}'.format(title,computation[2].get_raw_log_entries(),                   
                                                                                computation[2].output,computation[2].is_success,         
                                                                                computation[2].return_data,msg.code          
                                                                            )) 
    except Exception as ex:                  
        print('{}::msg={} err {}'.format(title,dir(msg),ex))
                                                       
db = AtomicDB() #MemoryDB()                                                       
#vm = FrontierVM(constants.GENESIS_BLOCK_NUMBER, db)
#chain = Chain(vm)
sender_private_key = keys.PrivateKey(to_bytes(hexstr='0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8'))
sender_address = sender_private_key.public_key.to_canonical_address()


SOME_ADDRESS = b'\x85\x82\xa2\x89V\xb9%\x93M\x03\xdd\xb4Xu\xe1\x8e\x85\x93\x12\xc1'
SOME_ADDRESS1 = b'\x85\x82\xa2\x89V\xb9%\x93M\x03\xdd\xb4Xu\xe1\x8e\x85\x93\x12\xc2'

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


chain = MiningChain.configure( # RopstenChain.configure( #
    __name__='MyChain',
    
    vm_configuration=((constants.GENESIS_BLOCK_NUMBER, FrontierVM),),
    #consensus_context=consensus,
    chain_id=1,
).from_genesis(db,GENESIS_PARAMS,GENESIS_STATE)
genesis = chain.get_canonical_block_header_by_number(0)

vm = chain.get_vm()
changes = vm.state
print('genesis',genesis,dir(db)#,dir(chain),'adb',dir(vm.state._account_db),'\nACC',vm.state._account_db.account_exists(SOME_ADDRESS)
      )
# before transaction
bal,bal1 = changes.get_balance(SOME_ADDRESS),changes.get_balance(sender_address)
print('SOME bal',bal,'\nSOME bal',bal1)

sender_private_key = keys.PrivateKey(to_bytes(hexstr='0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8'))
sender_address = sender_private_key.public_key.to_canonical_address()

contract_address = to_bytes(hexstr='0x742d35Cc6634C0532925a3b844Bc454e4438f44e')
transaction = chain.create_unsigned_transaction(
    nonce=vm.state.get_nonce(sender_address),
    gas_price=1,#vm.state.get_gas_price(),
    gas=21000,  # Здесь можно указать другое значение газа
    to=SOME_ADDRESS,#b'\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\x02',
    value=to_wei(0.5, 'ether'),  # Здесь можно указать другое количество ETH
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

root0 = vm.state.state_root
signed_tx = transaction.as_signed_transaction(sender_private_key)
if False:
    block = vm.mine_block(
       coinbase=sender_address,
       transactions=[signed_tx],
    )
    chain.apply_block(block)

if False:
    ex = vm.state.get_transaction_executor()
    print('EXEC',ex,dir(ex))
    comp = ex.validate_transaction(signed_tx)
    print('comp',comp)


comp0 = chain.apply_transaction(signed_tx)
#vm.state.commit()
root1 = vm.state.state_root
st1 = type(vm.state.commit)
print('ROOT',root0.hex(),st1)
print('ROOT',root1.hex(),root0 == root1)

check_computation(comp0,"COMP0")

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
    transaction1 = chain.create_unsigned_transaction(                                                                                   
        nonce=1,#vm.state.get_nonce(sender_address),                                                                                    
        gas_price=gas_price,#1,#vm.state.get_gas_price(),                                                                               
        gas=gas_limit,#21000,  # Здесь можно указать другое значение газа                                                               
        to = b'',# b'\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\x00',  # В этом случае контракт будет развернут, поэтому адрес None               
        value=0,#to_wei(0.5, 'ether'),                                                                                                  
        data = contract_bytecode,                                                                                                       
    )                                                                                                                                   
    signed_tx1 = transaction1.as_signed_transaction(sender_private_key)

    function_set_abi = [{"inputs":[{"internalType":"uint256","name":"x","type":"uint256"}],"name":"set","outputs":[],"stateMutability":"nonpayable","type":"function"}]
    f_get_abi = [{"inputs":[],"name":"get","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]
    args = []
    selector = encode_abi(['uint256'], [12345])#encode_abi(['function'], [function_set_abi]).hex()[:10]
    #function_selector = encode_abi(['bytes4', 'uint256'], ['set(uint256)', [123]])

    print('SELECTOR',selector)
    method_signature = ['get()'.encode()]
    method_arguments = [            ]
    selector1 = encode_abi(['bytes'], ['get()'.encode()])
    selector = binascii.unhexlify('60fe47b1')
    print('selector',selector,selector1)

    
    root0 = vm.state.state_root
    comp1 = chain.apply_transaction(signed_tx1)
    root1 = vm.state.state_root
    print('ROOT',root0.hex())
    print('ROOT',root1.hex(),root0 == root1)
    check_computation(comp1,"COMP1>>")
    addr_contr  =comp1[2].msg.storage_address
    print('addr_contr',addr_contr)
    transaction2 = chain.create_unsigned_transaction(
    nonce=2,#vm.state.get_nonce(sender_address),
    gas_price=1,#1,#vm.state.get_gas_price(),
    gas=100000,#21000,  # Здесь можно указать другое значение газа
    to = addr_contr,  # В этом случае контракт будет развернут, поэтому адрес None
    value=0,#to_wei(0.5, 'ether'),
    data = selector,
    )
    signed_tx2 = transaction2.as_signed_transaction(sender_private_key)
    comp2 = chain.apply_transaction(signed_tx2)
    check_computation(comp2,"COMP2")
    bal1 = changes.get_balance(addr_contr)
    print('bal1',bal1)
    data= db.get(addr_contr)
    print('DATA',data)




block_result = vm.finalize_block(chain.get_block())
block = block_result.block
print('block',block)


balance = vm.state.get_balance(sender_address) 
print("balance ",balance,sender_address)
bal = changes.get_balance(SOME_ADDRESS)
print('SOME bal',bal,vm.state.state_root)
#for key in db.keys() :
#    print('db:key {}'.format(key))
print('keys',db.items())

