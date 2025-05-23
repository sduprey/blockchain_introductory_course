// SPDX-License-Identifier: MIT
pragma solidity >=0.8.2 <0.9.0;

contract Base{
    uint public a;
    constructor(){
        a=1;
    }
    function foo() virtual public {
        a +=2;
    }
}
contract Sub is Base {
    uint public b;
    constructor() Base(){
        b=2;
    }
    
    function foo() override public {
        super.foo();
        a+=1;
    }
}
