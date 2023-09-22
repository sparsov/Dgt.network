// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;
//pragma experimental ABIEncoderV2;
//pragma experimental SMTChecker;
//pragma experimental "v0.7.0";
contract HelloWorld {
    //uint256 public storedData;
    // Публичная функция, которая возвращает "Hello, World!"
    function sayHello() public pure returns (string memory) {
        return "Hello, World!";
    }
    function sayWorld() public pure returns (string memory) {
        return "World!";
    }
}
