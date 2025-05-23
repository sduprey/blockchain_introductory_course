// SPDX-License-Identifier: MIT
pragma solidity >=0.8.2 <0.9.0;

contract FeeCollector{
    address public owner;
    uint256 public balance;
    
    event Withdraw(address indexed to, uint256 amount); 

    constructor(){
        owner=msg.sender;
    }

    receive() external payable {
        balance += msg.value;
    }
    
    function withdraw(uint amount, address payable destAdr) public {
        require(msg.sender==owner, "Only owner can withdraw");
        require(amount <= balance, "Insufficient funds");
        destAdr.transfer(amount);
        balance -=amount;
    }
}