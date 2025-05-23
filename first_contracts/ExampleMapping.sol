// SPDX-License-Identifier: MIT
pragma solidity >=0.8.2 <0.9.0;

contract ExampleMapping{
    mapping(uint => string) public myMapping;
    mapping(uint => mapping(uint =>string)) public myNestedMapping;

    function get(uint id) public view returns (string memory) {
        return myMapping[id];
    }
    
    function set(uint id1,uint id2, string memory value) public {
        myNestedMapping[id1][id2] = value;
    }
    function remove(uint id1, uint id2) public {
        delete  myNestedMapping[id1][id2];
    }
}