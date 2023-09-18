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
import logging

logging.basicConfig(level=8) #logging.DEBUG)
logging.debug("Start test")
sender_private_key = keys.PrivateKey(to_bytes(hexstr='0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8'))
sender_address = sender_private_key.public_key.to_canonical_address()
some_private_key = keys.PrivateKey(to_bytes(hexstr='0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2ff'))
SOME_ADDRESS = some_private_key.public_key.to_canonical_address()
tx_nonce = 0


def check_computation(computation,title="computation"):
    msg= computation[2].msg   
    receipt  = computation[1]                                                                                                   
    addr_contr = msg.storage_address                                                                                                  
    print('{}:: {} msg={} storage_addr={} caddr={} stv={} val={} data={} ISC={}'.format(title,computation,msg,msg.storage_address,         
                                                                  msg.code_address,msg.should_transfer_value,msg.value,msg.data.hex(),      
                                                                  msg.is_create                                                       
                                                                  )) 
    try:
        print('{}:: GAS_USED={} REMAIN={} PRECOMP={}'.format(title,receipt.gas_used,computation[2].get_gas_remaining(),        
                                                                     computation[2].get_precompiles())) 
    except Exception as ex:
        print('{}:: err {}'.format(title,ex))
    try:
        print('{}:: RAW ENTRIES={}   OUT={} SUCCESS={} RET={} CODE={}'.format(title,computation[2].get_raw_log_entries(),                   
                                                                                computation[2].output,computation[2].is_success,         
                                                                                computation[2].return_data,msg.code          
                                                                            )) 
    except Exception as ex:                  
        print('{}::msg={} err {}'.format(title,dir(msg),ex))
                                                       
        
def send2add(sender_private_key,to_address,val):
    global tx_nonce
    sender_address = sender_private_key.public_key.to_canonical_address()
    print('tx_nonce',tx_nonce)
    transaction = chain.create_unsigned_transaction(                                                              
        nonce=vm.state.get_nonce(sender_address),                                                                     
        gas_price=1,#vm.state.get_gas_price(),                                                                        
        gas=21000,  # Здесь можно указать другое значение газа                                                        
        to=to_address,#b'\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\x02',                                               
        value=to_wei(val, 'ether'),  # Здесь можно указать другое количество ETH                                       
        data=b'',                                                                                                     
        #v=chain.network_id,                                                                                          
        #r=0,                                                                                                         
        #s=0,                                                                                                         
    ) 
    signed_tx = transaction.as_signed_transaction(sender_private_key)
    comp = chain.apply_transaction(signed_tx) 
    #tx_nonce = tx_nonce + 1
    return comp                                                                                                                
        
                                                               
db = AtomicDB() #MemoryDB()                                                       
#vm = FrontierVM(constants.GENESIS_BLOCK_NUMBER, db)
#chain = Chain(vm)


#SOME_ADDRESS = b'\x85\x82\xa2\x89V\xb9%\x93M\x03\xdd\xb4Xu\xe1\x8e\x85\x93\x12\xc1'
#SOME_ADDRESS1 = b'\x85\x82\xa2\x89V\xb9%\x93M\x03\xdd\xb4Xu\xe1\x8e\x85\x93\x12\xc2'

GENESIS_STATE = {

    SOME_ADDRESS: {

        "balance": to_wei(5000000, 'ether'),

        "nonce": 0,

        "code": b'',

        "storage": {}

    },
    sender_address: {

        "balance": to_wei(5000000, 'ether'), #int(5000000 * (10 ** 18)) ,#to_wei(10000000, 'ether'),

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
print('genesis',genesis,'\nVMSTATE',dir(vm.state)#,'adb',dir(vm.state._account_db),'\nACC',vm.state._account_db.account_exists(SOME_ADDRESS)
      )
# before transaction
bal,bal1 = changes.get_balance(SOME_ADDRESS),changes.get_balance(sender_address)
print('SOME bal',bal,'\nSOME bal',bal1)


contract_address = to_bytes(hexstr='0x742d35Cc6634C0532925a3b844Bc454e4438f44e')


comp0 = send2add(sender_private_key,SOME_ADDRESS,10)
check_computation(comp0,"SEND COMP0 >>")
comp0 = send2add(some_private_key,sender_address,10)
check_computation(comp0,"COMP0 >>")
#comp0 = send2add(some_private_key,sender_address,10)

contract_address = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"  # Address for your contract
contract_address = binascii.unhexlify('742d35Cc6634C0532925a3b844Bc454e4438f44e')
contract_address = constants.CREATE_CONTRACT_ADDRESS
smart_fnm = "./HelloWorld.bin" # 
#smart_fnm = './SimpleStorage.bin'
with open(smart_fnm, 'rb') as f:
    contract_bytecode = f.read()

#print('CONTR',len(contract_bytecode),contract_bytecode.hex())
# Create a new transaction to deploy the contract
# Создать объект транзакции
gas_price = 0  # Укажите желаемую цену газа
gas_limit = 73921+2454+22514+2402  # Укажите желаемый лимит газа
#gas_limit = 91139+2402+10000
root0 = vm.state.state_root

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


bal= vm.state._account_db.get_balance(sender_address)
print('BAL',bal)

#vm.state.commit()
root1 = vm.state.state_root
st1 = type(vm.state.commit)
print('ROOT',root0.hex(),st1)
print('ROOT',root1.hex(),root0 == root1)



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
    nonce_val = 1 
    transaction1 = chain.create_unsigned_transaction(                                                                                   
        nonce=nonce_val,#vm.state.get_nonce(sender_address),                                                                                    
        gas_price=gas_price,#1,#vm.state.get_gas_price(),                                                                               
        gas=gas_limit,#21000,  # Здесь можно указать другое значение газа                                                               
        to = contract_address,#b'\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\x00',  # В этом случае контракт будет развернут, поэтому адрес None               
        value=0,#to_wei(0.5, 'ether'),                                                                                                  
        data = contract_bytecode,                                                                                                       
    )                                                                                                                                   
    signed_tx1 = transaction1.as_signed_transaction(sender_private_key)

    function_set_abi = [{"inputs":[{"internalType":"uint256","name":"x","type":"uint256"}],"name":"set","outputs":[],"stateMutability":"nonpayable","type":"function"}]
    f_get_abi = [{"inputs":[],"name":"get","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]
    args = []
    selector = encode_abi(['uint256'], [12345])#encode_abi(['function'], [function_set_abi]).hex()[:10]
    #function_selector = encode_abi(['bytes4', 'uint256'], ['set(uint256)', [123]])

    #print('SELECTOR',selector)
    method_signature = ['get()'.encode()]
    method_arguments = [            ]
    selector1 = encode_abi(['bytes'], ['get()'.encode()])
    selector = binascii.unhexlify('60fe47b1')
    selector = decode_hex('0xef5fb05b')#: sayHello()
    print('selector',selector,selector1)

    
    root0 = vm.state.state_root
    print("LOAD SMART>>>")
    comp1 = chain.apply_transaction(signed_tx1)
    check_computation(comp1,"COMP1>>")
    addr_contr  =comp1[2].msg.storage_address
    print('ADDR_CONTR>>>',addr_contr,contract_address,addr_contr==contract_address)
    #vm.finalize_block(chain.get_block())
    bal1 = changes.get_balance(addr_contr)
    print('BAL1',bal1)

    if False:
        nonce_val += 1
        transaction1 = chain.create_unsigned_transaction(                                                                                   
            nonce=nonce_val,#vm.state.get_nonce(sender_address),                                                                                    
            gas_price=gas_price,#1,#vm.state.get_gas_price(),                                                                               
            gas=gas_limit,#21000,  # Здесь можно указать другое значение газа                                                               
            to = constants.CREATE_CONTRACT_ADDRESS,#contract_address,#b'\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\x00',  # В этом случае контракт будет развернут, поэтому адрес None               
            value=0,#to_wei(0.5, 'ether'),                                                                                                  
            data = contract_bytecode,                                                                                                       
        )                                                                                                                                   
        signed_tx1 = transaction1.as_signed_transaction(sender_private_key)
        comp1 = chain.apply_transaction(signed_tx1)
        slot = vm.state.get_code(contract_address) #contract_address,1)
        print('SLOT',slot)
        root1 = vm.state.state_root
        print('ROOT',root0.hex())
        print('ROOT',root1.hex(),root0 == root1)
        check_computation(comp1,"COMP1 DUP>>")
        addr_contr  =comp1[2].msg.storage_address
        print('ADDR_CONTR>>>',addr_contr,contract_address,addr_contr==contract_address)

    nonce_val += 1
    transaction2 = chain.create_unsigned_transaction(
        nonce=nonce_val,#vm.state.get_nonce(sender_address),
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
#for key,data in vm.state._db.items() :
#    print('db:key {}'.format(key))
print('keys',vm.state._db.items())

