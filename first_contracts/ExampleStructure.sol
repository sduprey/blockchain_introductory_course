// SPDX-License-Identifier: MIT
pragma solidity >=0.8.2 <0.9.0;

contract ExampleStructure{
    struct Data {
        uint a;
        bytes3 b;
        mapping (uint=>uint) map;
    }
    mapping (uint => mapping(bool => Data[])) public data;

    function getData(uint arg1,bool arg2,uint arg3) public view returns (uint a, bytes3 b){
        a = data[arg1][arg2][arg3].a;
        b = data[arg1][arg2][arg3].b;
        return (a,b);
    }

}