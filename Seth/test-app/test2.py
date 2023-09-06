from eth.vm.forks.frontier.blocks import FrontierBlock
from eth_keys import keys
from eth_utils import decode_hex, to_wei
from eth import constants

from eth.chains.mainnet import MainnetChain

from eth.db.atomic import AtomicDB
from eth_tester import EthereumTester, PyEVMBackend
# Создаем базу данных для цепи
#db = MemoryDB()

# Создаем экземпляр цепи
#chain = RopstenChain.from_genesis(db, SpuriousDragonVM)
SOME_ADDRESS = b'\x85\x82\xa2\x89V\xb9%\x93M\x03\xdd\xb4Xu\xe1\x8e\x85\x93\x12\xc1'

GENESIS_STATE = {

    SOME_ADDRESS: {

        "balance": to_wei(10000, 'ether'),

        "nonce": 0,

        "code": b'',

        "storage": {}

    }

}

GENESIS_PARAMS = {

    'difficulty': constants.GENESIS_DIFFICULTY,

}

chain = MainnetChain.from_genesis(AtomicDB(), GENESIS_PARAMS, GENESIS_STATE)
# Указать параметры транзакции
private_key_hex = "0x0123456789012345678901234567890123456789012345678901234567890123"  # Приватный ключ отправителя
sender_address_hex = "0x90F8bf6A479f320ead074411a4B0e7944Ea8c9C1"  # Адрес отправителя
#contract_bytecode = "0x606060... ваш байткод ..."  # Байткод вашего контракта
gas_limit = 2000000
gas_price = 1
nonce = 0  # Указать правильный nonce

# Преобразовать ключ и адрес в байты
private_key = decode_hex(private_key_hex)
sender_address = decode_hex(sender_address_hex)


# Подписать транзакцию
#signed_transaction = keys.PrivateKey(private_key).sign_transaction(transaction)

# Отправить транзакцию в цепь (здесь это опущено, так как это зависит от цепи)
# Важно: nonce должен быть правильным и уникальным для каждой транзакции отправителя

contract_bytecode = "0x606060405260648060106000396000f3606060405260e060020a6000350463c6888fa181146027578063d09de08a14603b575b600080fd5b603a602a60003504636d4ce63c8114605b578063f2fde38b14606d575b600080fd5b604160415060028a8560405183529190600a90825261000f91600491909101906100d6565b604051809103906000f080158015610079573d6000803e3d6000fd5b506001600160a01b0381351690602001356100a6565b60408051808201825260156100d191600483018190525060409001905080808501906020018083838290600060046020846101000a81548173ffffffffffffffffffffffffffffffffffffffff021916908373ffffffffffffffffffffffffffffffffffffffff16021790555050565b60408051808201825260156101c391600483018190525060409001905080808501906020018083838290600060046020846101000a81548173ffffffffffffffffffffffffffffffffffffffff021916908373ffffffffffffffffffffffffffffffffffffffff16021790555050565b6000805490509056fea165627a7a72305820d5c99d6e85ff2ec6093ca010ea5c14380b2a69f0ee81683aa325295ec3bdc740029"
contract_address = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"  # Address for your contract
sender_address = "0x90F8bf6A479f320ead074411a4B0e7944Ea8c9C1"  # Address of the sender

# Create a new transaction to deploy the contract
# Создать объект транзакции
transaction = {
    "nonce": nonce,
    "gas_price": gas_price,
    "gas": gas_limit,
    "to": None,  # В этом случае контракт будет развернут, поэтому адрес None
    "value": 0,
    "data": contract_bytecode,
}


# Create a new block to include the transaction
block = FrontierBlock(
    parent_header_hash=chain.get_canonical_head().hash,
    number=chain.get_canonical_head().block_number + 1,
    coinbase=sender_address,
    gas_limit=gas_limit,
    timestamp=0,#chain.get_vm()._block.timestamp,
    difficulty=constants.GENESIS_DIFFICULTY ,#chain.get_vm().block.difficulty,
)

# Add the transaction to the block
block = chain.apply_transaction(block, transaction)

# Deploy the contract
chain.mine_block(block)

# Get the contract instance
contract_instance = chain.get_contract(contract_address)
