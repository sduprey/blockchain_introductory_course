// SPDX-License-Identifier: MIT
pragma solidity >=0.8.2 <0.9.0;

contract ExampleLocalGlobal{
    address public contractAddress;
    address public payer;
    address public origin;
    uint public amount;

    constructor() {
        contractAddress = address(this); // the current contract address, if this is called by another smart contract it will use that as a reference
    }

    function pay() public payable {
        payer = msg.sender;
        origin = tx.origin;
        amount = msg.value;
    }

    function getBlockInfo() public view returns (uint, uint,uint) {
        return (block.number, block.timestamp, block.difficulty);
    }

}