// SPDX-License-Identifier: MIT
pragma solidity >=0.8.2 <0.9.0;

contract ExampleError{
    error NotOwner();
    address owner;

    constructor(){
        owner = msg.sender;
    }


    function transferOwnership() public view {
        if (msg.sender != owner){  
            revert NotOwner();
        }
        require(msg.sender == owner, "caller is not a Owner");
    }
}