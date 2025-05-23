// SPDX-License-Identifier: MIT
pragma solidity >=0.8.2 <0.9.0;

contract ExampleDataType{
    string text = "abc";
    bool isValid = false;
    uint constant x = 32**22+8;
    // cannot be changed
    bytes32 constant myHash = keccak256("abc");
    // cannot be changed after first instantiation
    uint immutable decimals;
    uint immutable maxBalance;
    address public balance;


    constructor(uint _decimals, address _reference){
        decimals = _decimals;
        maxBalance = _reference.balance;
    }

//    function set() public {
//        decimals = 1;
//    }


}