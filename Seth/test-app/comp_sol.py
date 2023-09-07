import solc as solcx
import json

# Установите версию Solidity
# solcx.install_solc("0.8.0")

# Определите исходный код смарт-контракта
source_code = """
// Пример смарт-контракта на Solidity
pragma solidity ^0.8.0;

contract SimpleStorage {
    uint256 public storedData;

    function set(uint256 x) public {
        storedData = x;
    }

    function get() public view returns (uint256) {
        return storedData;
    }
}
"""

# Скомпилируйте контракт
compiled_contract = solcx.compile_source(source_code)

# Получите байткод контракта и ABI
bytecode = compiled_contract["<stdin>:SimpleStorage"]["bin"]
abi = json.loads(compiled_contract["<stdin>:SimpleStorage"]["abi"])

# Выведите байткод и ABI
print("Bytecode:")
print(bytecode)
print("\nABI:")
print(json.dumps(abi, indent=4))
