// SPDX-License-Identifier: MIT
pragma solidity >=0.8.2 <0.9.0;

contract ExampleFunctionModifier{

    address public balance;
    string public name = "balance";

    // view: can only read state and cannot modify it
    function getName() public view returns (string memory) {return name;}

    //pure: can't read or write the state
    function add (uint a, uint b) public pure returns (uint){ return a+b;}

    //payable : accept ether
    function pay() public payable {
        
    }

}