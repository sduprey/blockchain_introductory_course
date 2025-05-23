// SPDX-License-Identifier: MIT
pragma solidity >=0.8.2 <0.9.0;

contract Counter{
    uint public counter;

    constructor(){
        counter=0;
    }

    function count() public {
        counter = counter + 1;
    }

    function get() public view returns (uint){
        return counter;
    }
}