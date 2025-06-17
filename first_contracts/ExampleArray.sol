// SPDX-License-Identifier: MIT
pragma solidity >=0.8.2 <0.9.0;

contract ExampleArray{
    //variable size array
    uint[] public numbers = [1,5,7,3];
    //fixed size array
    uint[1] public anotherArray= [1];
    function test() public {
        numbers.push(1);
        //anotherArray.push(1);
        numbers.pop();
        numbers[0];
        numbers.length;
    }
}