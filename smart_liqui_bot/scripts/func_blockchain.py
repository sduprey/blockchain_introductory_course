#!/usr/bin/env python
# coding: utf-8
import json
from web3 import Web3
from eth_abi import encode
import requests
import json
from datetime import datetime
from decimal import Decimal

def send_slack_message(message,incoming_web_hook=None):
    payload = '{"text":"%s"}'% message
    response = requests.post(incoming_web_hook, data=payload)
    print(response.text)

def get_max_gas_fee(url = None):
    payload = {
        "id": 1,
        "jsonrpc": "2.0",
        "method": "eth_gasPrice"
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json"
    }
    response = requests.post(url, json=payload, headers=headers)
    hex_string = json.loads(response.text)['result']
    dec = int(hex_string, 16)
    return dec

def get_max_priority_fee(url = None):
    payload = {
        "id": 1,
        "jsonrpc": "2.0",
        "method": "eth_maxPriorityFeePerGas"
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)
    hex_string = json.loads(response.text)['result']
    dec = int(hex_string, 16)
    return dec

def trigger_add_oracle(lower_tick = None, upper_tick = None, position_manager_address = None, oracle_key=None, default_gas_limit_add = 500000, add_data='0x759b7163',rpcEndPoint = None, max_priority_fee = None, max_gas_fee=None, incoming_web_hook=None):
    w3 = Web3(Web3.HTTPProvider(rpcEndPoint))
    oracle_account = w3.eth.account.from_key(oracle_key)
    oracle_account_address = oracle_account.address
    encoded_params_bytes = encode(['int24', 'int24'], [lower_tick, upper_tick])
    encoded_params = str(w3.toHex(encoded_params_bytes))
    tx = {
        'type': '0x2',
        'nonce': w3.eth.getTransactionCount(oracle_account_address),
        'from': oracle_account_address,
        'to': position_manager_address,
        'data':add_data +encoded_params.replace('0x','') ,
        'maxFeePerGas': max_gas_fee,
        'maxPriorityFeePerGas': max_priority_fee,
        'chainId': 1
    }
    #gas = w3.eth.estimateGas(tx) # gas limit
    tx['gas'] = default_gas_limit_add
    signed_tx = w3.eth.account.signTransaction(tx, oracle_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    transac_submit_dictionary = {
        'status': 'just submitted',
        'tx_hash': str(w3.toHex(tx_hash)),
        'max_gas_fee': max_gas_fee,
        'max_priority_fee': max_priority_fee,
        'type': 'add_liquidity'
    }
    payload_message = json.dumps(transac_submit_dictionary)
    payload_message = payload_message.replace('"', '')
    payload_message = 'Production smart liquidity transaction submission payload : ' + payload_message
    send_slack_message(payload_message, incoming_web_hook=incoming_web_hook)
    print(payload_message)

    tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
    if tx_receipt['status'] == 1:
        print('liquidity added successfully! Hash: {}'.format(str(w3.toHex(tx_hash))))
    else:
        print('There was an error removing liquidity')
    return tx_receipt['status'], str(w3.toHex(tx_hash))


def trigger_remove_oracle(rebalance = False, position_manager_address = None, oracle_key=None, default_gas_limit_remove = 300000, remove_data='0x67b9a286',rpcEndPoint =None, max_priority_fee=None, max_gas_fee=None, incoming_web_hook=None):
    w3 = Web3(Web3.HTTPProvider(rpcEndPoint))
    oracle_account = w3.eth.account.from_key(oracle_key)
    oracle_account_address = oracle_account.address

    encoded_params_bytes = encode(['bool'], [rebalance])
    encoded_params = str(w3.toHex(encoded_params_bytes))

    tx = {
        'type': '0x2',
        'nonce': w3.eth.getTransactionCount(oracle_account_address),
        'from': oracle_account_address,
        'to': position_manager_address,
        'data':remove_data+encoded_params.replace('0x',''),
        'maxFeePerGas': max_gas_fee,
        'maxPriorityFeePerGas': max_priority_fee,
        'chainId': 1
    }
    #gas = w3.eth.estimateGas(tx) # gas limit
    tx['gas'] = default_gas_limit_remove
    signed_tx = w3.eth.account.signTransaction(tx, oracle_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

    transac_submit_dictionary = {
        'status': 'just submitted',
        'tx_hash': str(w3.toHex(tx_hash)),
        'max_gas_fee': max_gas_fee,
        'max_priority_fee': max_priority_fee,
        'type': 'remove_liquidity'
    }
    payload_message = json.dumps(transac_submit_dictionary)
    payload_message = payload_message.replace('"', '')
    payload_message = 'Production smart liquidity transaction submission payload : ' + payload_message
    send_slack_message(payload_message, incoming_web_hook=incoming_web_hook)
    print(payload_message)

    tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
    if tx_receipt['status'] == 1:
        print('liquidity remove successfully! Hash: {}'.format(str(w3.toHex(tx_hash))))
    else:
        print('There was an error removing liquidity')
    return tx_receipt['status'], str(w3.toHex(tx_hash))




class BlockchainAgent:
    def __init__(self):
        self.slack_hook = '**'
        ###polygon endpoint
        ###rpcEndPoint = 'https://polygon-mainnet.g.alchemy.com/v2/***'
        self.rpcEndPoint = 'https://eth-mainnet.g.alchemy.com/v2/****'
        #### polygon value
        #### _address = '0x4bE3a1A52223d333C689074706D13F7a56f1381A'
        #### mainnet value
        self.position_manager_address = '0x4C46799C2Bd7459bFEBF947b477E7d036ff6BE2F'
        self.oracle_key = '*****'
        self.default_gas_limit_add = 500000
        self.add_data = '0x759b7163'
        self.default_gas_limit_remove = 500000
        self.remove_data = '0xe12d91d8'
        self.api_key = '****'
        self.fees_multiplier = 1.4

    def rebalance_liquidity(self, lower_tick=None, upper_tick=None):
        ###### we remove liquidity
        remove_liquidity = True
        reequilibrate = True
        if remove_liquidity:
            max_gas_fee = get_max_gas_fee(url=self.rpcEndPoint)
            max_gas_fee = int(max_gas_fee * self.fees_multiplier)
            max_priority_fee = get_max_priority_fee(url=self.rpcEndPoint)
            status, tx_hash = trigger_remove_oracle(max_priority_fee=max_priority_fee, max_gas_fee=max_gas_fee,
                                                    position_manager_address=self.position_manager_address,
                                                    oracle_key=self.oracle_key,
                                                    rebalance=reequilibrate,
                                                    default_gas_limit_remove=self.default_gas_limit_remove,
                                                    remove_data=self.remove_data, rpcEndPoint=self.rpcEndPoint,
                                                    incoming_web_hook=self.slack_hook)
            transac_update_dictionary = {
                'status': status,
                'tx_hash': tx_hash,
                'max_gas_fee': max_gas_fee,
                'max_priority_fee': max_priority_fee,
                'type': 'remove_liquidity'
            }
            payload_message = json.dumps(transac_update_dictionary)
            payload_message = payload_message.replace('"', '')
            payload_message = 'Production smart liquidity transaction update payload : ' + payload_message
            send_slack_message(payload_message, incoming_web_hook=self.slack_hook)
            print(payload_message)
        add_liquidity = True
        if add_liquidity:
            max_gas_fee = get_max_gas_fee(url=self.rpcEndPoint)
            max_gas_fee = int(max_gas_fee * self.fees_multiplier)
            max_priority_fee = get_max_priority_fee(url=self.rpcEndPoint)
            status, tx_hash = trigger_add_oracle(lower_tick=lower_tick, upper_tick=upper_tick,
                                                 max_priority_fee=max_priority_fee, max_gas_fee=max_gas_fee,
                                                 position_manager_address=self.position_manager_address,
                                                 oracle_key=self.oracle_key, default_gas_limit_add=self.default_gas_limit_add,
                                                 add_data=self.add_data, rpcEndPoint=self.rpcEndPoint,
                                                 incoming_web_hook=self.slack_hook)
            transac_update_dictionary = {
                'status': status,
                'tx_hash': tx_hash,
                'max_gas_fee': max_gas_fee,
                'max_priority_fee': max_priority_fee,
                'type': 'add_liquidity'
            }
            payload_message = json.dumps(transac_update_dictionary)
            payload_message = payload_message.replace('"', '')
            payload_message = 'Production smart liquidity transaction update payload : ' + payload_message
            send_slack_message(payload_message, incoming_web_hook=self.slack_hook)
            print(payload_message)
        return

    def manage_liquidity(self, raw_generated_signal=None, raw_previous_signal=None, lower_tick=None, upper_tick=None, reequilibrate = False):
        if raw_generated_signal > 0 and abs(raw_previous_signal) < 1e-4:
            max_gas_fee = get_max_gas_fee(url=self.rpcEndPoint)
            max_gas_fee = int(max_gas_fee * self.fees_multiplier)
            max_priority_fee = get_max_priority_fee(url=self.rpcEndPoint)
            status, tx_hash = trigger_add_oracle(lower_tick=lower_tick, upper_tick=upper_tick,
                                                 max_priority_fee=max_priority_fee, max_gas_fee=max_gas_fee,
                                                 position_manager_address=self.position_manager_address,
                                                 oracle_key=self.oracle_key, default_gas_limit_add=self.default_gas_limit_add,
                                                 add_data=self.add_data, rpcEndPoint=self.rpcEndPoint,
                                                 incoming_web_hook=self.slack_hook)
            transac_update_dictionary = {
                'status': status,
                'tx_hash': tx_hash,
                'max_gas_fee': max_gas_fee,
                'max_priority_fee': max_priority_fee,
                'type': 'add_liquidity'
            }
            payload_message = json.dumps(transac_update_dictionary)
            payload_message = payload_message.replace('"', '')
            payload_message = 'Production smart liquidity transaction update payload : ' + payload_message
            send_slack_message(payload_message, incoming_web_hook=self.slack_hook)
            print(payload_message)

        if abs(raw_generated_signal) < 1e-4 and raw_previous_signal > 0:
            max_gas_fee = get_max_gas_fee(url=self.rpcEndPoint)
            max_gas_fee = int(max_gas_fee * self.fees_multiplier)
            max_priority_fee = get_max_priority_fee(url=self.rpcEndPoint)
            status, tx_hash = trigger_remove_oracle(max_priority_fee=max_priority_fee, max_gas_fee=max_gas_fee,
                                                    position_manager_address=self.position_manager_address,
                                                    oracle_key=self.oracle_key,
                                                    rebalance=reequilibrate,
                                                    default_gas_limit_remove=self.default_gas_limit_remove,
                                                    remove_data=self.remove_data, rpcEndPoint=self.rpcEndPoint,
                                                    incoming_web_hook=self.slack_hook)
            transac_update_dictionary = {
                'status': status,
                'tx_hash': tx_hash,
                'max_gas_fee': max_gas_fee,
                'max_priority_fee': max_priority_fee,
                'type': 'remove_liquidity'
            }
            payload_message = json.dumps(transac_update_dictionary)
            payload_message = payload_message.replace('"', '')
            payload_message = 'Production smart liquidity transaction update payload : ' + payload_message
            send_slack_message(payload_message, incoming_web_hook=self.slack_hook)
            print(payload_message)
        return

class MetricsAgent:
    def __init__(self):
        self.slack_hook = '***'
        ###polygon endpoint
        ###rpcEndPoint = 'https://polygon-mainnet.g.alchemy.com/v2/-h8MEFOHDX8ab4XoPNMPykjH6zThFo6i'
        self.rpcEndPoint = 'https://eth-mainnet.g.alchemy.com/v2/CNKEcaWfrT_qMGP-m9N8N-Cc0rjJ3sTj'
        #### polygon value
        #### _address = '0x4bE3a1A52223d333C689074706D13F7a56f1381A'
        #### mainnet value
        self.position_manager_contract_address = Web3.toChecksumAddress(
            "0x4c46799c2bd7459bfebf947b477e7d036ff6be2f")
        self.helper_contract_address = Web3.toChecksumAddress("0x07d2CeB4869DFE17e8D48c92A71eDC3AE564449f")
        position_manager_abi = [
            {
                "anonymous": False,
                "inputs": [
                    {
                        "indexed": False,
                        "internalType": "address",
                        "name": "previousAdmin",
                        "type": "address"
                    },
                    {
                        "indexed": False,
                        "internalType": "address",
                        "name": "newAdmin",
                        "type": "address"
                    }
                ],
                "name": "AdminChanged",
                "type": "event"
            },
            {
                "anonymous": False,
                "inputs": [
                    {
                        "indexed": True,
                        "internalType": "address",
                        "name": "beacon",
                        "type": "address"
                    }
                ],
                "name": "BeaconUpgraded",
                "type": "event"
            },
            {
                "anonymous": False,
                "inputs": [
                    {
                        "indexed": False,
                        "internalType": "uint8",
                        "name": "version",
                        "type": "uint8"
                    }
                ],
                "name": "Initialized",
                "type": "event"
            },
            {
                "anonymous": False,
                "inputs": [
                    {
                        "indexed": False,
                        "internalType": "int24",
                        "name": "tickLower",
                        "type": "int24"
                    },
                    {
                        "indexed": False,
                        "internalType": "int24",
                        "name": "tickUpper",
                        "type": "int24"
                    }
                ],
                "name": "LiquidityAdded",
                "type": "event"
            },
            {
                "anonymous": False,
                "inputs": [],
                "name": "LiquidityRemoved",
                "type": "event"
            },
            {
                "anonymous": False,
                "inputs": [
                    {
                        "indexed": True,
                        "internalType": "address",
                        "name": "previousOwner",
                        "type": "address"
                    },
                    {
                        "indexed": True,
                        "internalType": "address",
                        "name": "newOwner",
                        "type": "address"
                    }
                ],
                "name": "OwnershipTransferred",
                "type": "event"
            },
            {
                "anonymous": False,
                "inputs": [
                    {
                        "indexed": True,
                        "internalType": "address",
                        "name": "implementation",
                        "type": "address"
                    }
                ],
                "name": "Upgraded",
                "type": "event"
            },
            {
                "inputs": [
                    {
                        "internalType": "int24",
                        "name": "_lT",
                        "type": "int24"
                    },
                    {
                        "internalType": "int24",
                        "name": "_uT",
                        "type": "int24"
                    }
                ],
                "name": "addLiquidityInRange",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "arrakisv2Resolver",
                "outputs": [
                    {
                        "internalType": "address",
                        "name": "",
                        "type": "address"
                    }
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "arrakisv2Vault",
                "outputs": [
                    {
                        "internalType": "address",
                        "name": "",
                        "type": "address"
                    }
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [
                    {
                        "internalType": "uint256",
                        "name": "_slippageTolerance",
                        "type": "uint256"
                    }
                ],
                "name": "backToEquilibrium",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "burn",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    {
                        "internalType": "address",
                        "name": "_coin",
                        "type": "address"
                    }
                ],
                "name": "collect",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "getImplementation",
                "outputs": [
                    {
                        "internalType": "address",
                        "name": "",
                        "type": "address"
                    }
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [
                    {
                        "internalType": "address",
                        "name": "_arrakisv2vault",
                        "type": "address"
                    },
                    {
                        "internalType": "address",
                        "name": "_arrakisv2Resolver",
                        "type": "address"
                    },
                    {
                        "internalType": "address",
                        "name": "_uniV3Pool",
                        "type": "address"
                    },
                    {
                        "internalType": "address",
                        "name": "_chainlinkPriceFeed",
                        "type": "address"
                    },
                    {
                        "internalType": "address",
                        "name": "_uniswapv3Router",
                        "type": "address"
                    }
                ],
                "name": "initialize",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "isLping",
                "outputs": [
                    {
                        "internalType": "bool",
                        "name": "",
                        "type": "bool"
                    }
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "manager",
                "outputs": [
                    {
                        "internalType": "address",
                        "name": "",
                        "type": "address"
                    }
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [
                    {
                        "internalType": "uint256",
                        "name": "usdcAmount",
                        "type": "uint256"
                    },
                    {
                        "internalType": "uint256",
                        "name": "wethAmount",
                        "type": "uint256"
                    }
                ],
                "name": "mint",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "owner",
                "outputs": [
                    {
                        "internalType": "address",
                        "name": "",
                        "type": "address"
                    }
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "proxiableUUID",
                "outputs": [
                    {
                        "internalType": "bytes32",
                        "name": "",
                        "type": "bytes32"
                    }
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [
                    {
                        "internalType": "bool",
                        "name": "_rebal",
                        "type": "bool"
                    }
                ],
                "name": "removeLiquidity",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "renounceOwnership",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    {
                        "internalType": "address",
                        "name": "_newResolver",
                        "type": "address"
                    }
                ],
                "name": "setArrakisResolver",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    {
                        "internalType": "address",
                        "name": "_newVault",
                        "type": "address"
                    }
                ],
                "name": "setArrakisV2Vault",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    {
                        "internalType": "address",
                        "name": "_newManager",
                        "type": "address"
                    }
                ],
                "name": "setManager",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "token0",
                "outputs": [
                    {
                        "internalType": "address",
                        "name": "",
                        "type": "address"
                    }
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "token1",
                "outputs": [
                    {
                        "internalType": "address",
                        "name": "",
                        "type": "address"
                    }
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [
                    {
                        "internalType": "address",
                        "name": "newOwner",
                        "type": "address"
                    }
                ],
                "name": "transferOwnership",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "uniV3Pool",
                "outputs": [
                    {
                        "internalType": "address",
                        "name": "",
                        "type": "address"
                    }
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "uniswapv3Router",
                "outputs": [
                    {
                        "internalType": "address",
                        "name": "",
                        "type": "address"
                    }
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [
                    {
                        "internalType": "address",
                        "name": "_newAdmin",
                        "type": "address"
                    }
                ],
                "name": "updateVaultAdmin",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    {
                        "internalType": "address",
                        "name": "_newManager",
                        "type": "address"
                    }
                ],
                "name": "updateVaultManager",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    {
                        "internalType": "address",
                        "name": "newImplementation",
                        "type": "address"
                    }
                ],
                "name": "upgradeTo",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    {
                        "internalType": "address",
                        "name": "newImplementation",
                        "type": "address"
                    },
                    {
                        "internalType": "bytes",
                        "name": "data",
                        "type": "bytes"
                    }
                ],
                "name": "upgradeToAndCall",
                "outputs": [],
                "stateMutability": "payable",
                "type": "function"
            },
            {
                "stateMutability": "payable",
                "type": "receive"
            }
        ]

        helper_abi = [
            {
                "inputs": [
                    {
                        "components": [
                            {
                                "internalType": "int24",
                                "name": "lowerTick",
                                "type": "int24"
                            },
                            {
                                "internalType": "int24",
                                "name": "upperTick",
                                "type": "int24"
                            },
                            {
                                "internalType": "uint24",
                                "name": "feeTier",
                                "type": "uint24"
                            }
                        ],
                        "internalType": "struct Range[]",
                        "name": "ranges_",
                        "type": "tuple[]"
                    },
                    {
                        "internalType": "address",
                        "name": "token0_",
                        "type": "address"
                    },
                    {
                        "internalType": "address",
                        "name": "token1_",
                        "type": "address"
                    },
                    {
                        "internalType": "address",
                        "name": "vaultV2_",
                        "type": "address"
                    }
                ],
                "name": "token0AndToken1ByRange",
                "outputs": [
                    {
                        "components": [
                            {
                                "components": [
                                    {
                                        "internalType": "int24",
                                        "name": "lowerTick",
                                        "type": "int24"
                                    },
                                    {
                                        "internalType": "int24",
                                        "name": "upperTick",
                                        "type": "int24"
                                    },
                                    {
                                        "internalType": "uint24",
                                        "name": "feeTier",
                                        "type": "uint24"
                                    }
                                ],
                                "internalType": "struct Range",
                                "name": "range",
                                "type": "tuple"
                            },
                            {
                                "internalType": "uint256",
                                "name": "amount",
                                "type": "uint256"
                            }
                        ],
                        "internalType": "struct Amount[]",
                        "name": "amount0s",
                        "type": "tuple[]"
                    },
                    {
                        "components": [
                            {
                                "components": [
                                    {
                                        "internalType": "int24",
                                        "name": "lowerTick",
                                        "type": "int24"
                                    },
                                    {
                                        "internalType": "int24",
                                        "name": "upperTick",
                                        "type": "int24"
                                    },
                                    {
                                        "internalType": "uint24",
                                        "name": "feeTier",
                                        "type": "uint24"
                                    }
                                ],
                                "internalType": "struct Range",
                                "name": "range",
                                "type": "tuple"
                            },
                            {
                                "internalType": "uint256",
                                "name": "amount",
                                "type": "uint256"
                            }
                        ],
                        "internalType": "struct Amount[]",
                        "name": "amount1s",
                        "type": "tuple[]"
                    }
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [
                    {
                        "components": [
                            {
                                "internalType": "int24",
                                "name": "lowerTick",
                                "type": "int24"
                            },
                            {
                                "internalType": "int24",
                                "name": "upperTick",
                                "type": "int24"
                            },
                            {
                                "internalType": "uint24",
                                "name": "feeTier",
                                "type": "uint24"
                            }
                        ],
                        "internalType": "struct Range[]",
                        "name": "ranges_",
                        "type": "tuple[]"
                    },
                    {
                        "internalType": "address",
                        "name": "token0_",
                        "type": "address"
                    },
                    {
                        "internalType": "address",
                        "name": "token1_",
                        "type": "address"
                    },
                    {
                        "internalType": "address",
                        "name": "vaultV2_",
                        "type": "address"
                    }
                ],
                "name": "token0AndToken1PlusFeesByRange",
                "outputs": [
                    {
                        "components": [
                            {
                                "components": [
                                    {
                                        "internalType": "int24",
                                        "name": "lowerTick",
                                        "type": "int24"
                                    },
                                    {
                                        "internalType": "int24",
                                        "name": "upperTick",
                                        "type": "int24"
                                    },
                                    {
                                        "internalType": "uint24",
                                        "name": "feeTier",
                                        "type": "uint24"
                                    }
                                ],
                                "internalType": "struct Range",
                                "name": "range",
                                "type": "tuple"
                            },
                            {
                                "internalType": "uint256",
                                "name": "amount",
                                "type": "uint256"
                            }
                        ],
                        "internalType": "struct Amount[]",
                        "name": "amount0s",
                        "type": "tuple[]"
                    },
                    {
                        "components": [
                            {
                                "components": [
                                    {
                                        "internalType": "int24",
                                        "name": "lowerTick",
                                        "type": "int24"
                                    },
                                    {
                                        "internalType": "int24",
                                        "name": "upperTick",
                                        "type": "int24"
                                    },
                                    {
                                        "internalType": "uint24",
                                        "name": "feeTier",
                                        "type": "uint24"
                                    }
                                ],
                                "internalType": "struct Range",
                                "name": "range",
                                "type": "tuple"
                            },
                            {
                                "internalType": "uint256",
                                "name": "amount",
                                "type": "uint256"
                            }
                        ],
                        "internalType": "struct Amount[]",
                        "name": "amount1s",
                        "type": "tuple[]"
                    },
                    {
                        "components": [
                            {
                                "components": [
                                    {
                                        "internalType": "int24",
                                        "name": "lowerTick",
                                        "type": "int24"
                                    },
                                    {
                                        "internalType": "int24",
                                        "name": "upperTick",
                                        "type": "int24"
                                    },
                                    {
                                        "internalType": "uint24",
                                        "name": "feeTier",
                                        "type": "uint24"
                                    }
                                ],
                                "internalType": "struct Range",
                                "name": "range",
                                "type": "tuple"
                            },
                            {
                                "internalType": "uint256",
                                "name": "amount",
                                "type": "uint256"
                            }
                        ],
                        "internalType": "struct Amount[]",
                        "name": "fee0s",
                        "type": "tuple[]"
                    },
                    {
                        "components": [
                            {
                                "components": [
                                    {
                                        "internalType": "int24",
                                        "name": "lowerTick",
                                        "type": "int24"
                                    },
                                    {
                                        "internalType": "int24",
                                        "name": "upperTick",
                                        "type": "int24"
                                    },
                                    {
                                        "internalType": "uint24",
                                        "name": "feeTier",
                                        "type": "uint24"
                                    }
                                ],
                                "internalType": "struct Range",
                                "name": "range",
                                "type": "tuple"
                            },
                            {
                                "internalType": "uint256",
                                "name": "amount",
                                "type": "uint256"
                            }
                        ],
                        "internalType": "struct Amount[]",
                        "name": "fee1s",
                        "type": "tuple[]"
                    }
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [
                    {
                        "internalType": "contract IArrakisV2",
                        "name": "vault_",
                        "type": "address"
                    }
                ],
                "name": "totalUnderlying",
                "outputs": [
                    {
                        "internalType": "uint256",
                        "name": "amount0",
                        "type": "uint256"
                    },
                    {
                        "internalType": "uint256",
                        "name": "amount1",
                        "type": "uint256"
                    }
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [
                    {
                        "internalType": "contract IArrakisV2",
                        "name": "vault_",
                        "type": "address"
                    }
                ],
                "name": "totalUnderlyingWithFees",
                "outputs": [
                    {
                        "internalType": "uint256",
                        "name": "amount0",
                        "type": "uint256"
                    },
                    {
                        "internalType": "uint256",
                        "name": "amount1",
                        "type": "uint256"
                    },
                    {
                        "internalType": "uint256",
                        "name": "fee0",
                        "type": "uint256"
                    },
                    {
                        "internalType": "uint256",
                        "name": "fee1",
                        "type": "uint256"
                    }
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [
                    {
                        "internalType": "contract IArrakisV2",
                        "name": "vault_",
                        "type": "address"
                    }
                ],
                "name": "totalUnderlyingWithFeesAndLeftOver",
                "outputs": [
                    {
                        "components": [
                            {
                                "internalType": "uint256",
                                "name": "amount0",
                                "type": "uint256"
                            },
                            {
                                "internalType": "uint256",
                                "name": "amount1",
                                "type": "uint256"
                            },
                            {
                                "internalType": "uint256",
                                "name": "fee0",
                                "type": "uint256"
                            },
                            {
                                "internalType": "uint256",
                                "name": "fee1",
                                "type": "uint256"
                            },
                            {
                                "internalType": "uint256",
                                "name": "leftOver0",
                                "type": "uint256"
                            },
                            {
                                "internalType": "uint256",
                                "name": "leftOver1",
                                "type": "uint256"
                            }
                        ],
                        "internalType": "struct UnderlyingOutput",
                        "name": "underlying",
                        "type": "tuple"
                    }
                ],
                "stateMutability": "view",
                "type": "function"
            }
        ]

        position_manager_abi_json_string = json.dumps(position_manager_abi)
        helper_abi_json_string = json.dumps(helper_abi)

        self.position_manager_abi_json_string=position_manager_abi_json_string
        self.helper_abi_json_string=helper_abi_json_string

    def output_metrics(self):
        # Create smart contract instance
        w3 = Web3(Web3.HTTPProvider(self.rpcEndPoint))
        position_manager_contract = w3.eth.contract(address=self.position_manager_contract_address,
                                                    abi=self.position_manager_abi_json_string)
        address_vault = position_manager_contract.functions.arrakisv2Vault().call()

        helper_contract = w3.eth.contract(address=self.helper_contract_address, abi=self.helper_abi_json_string)
        results = helper_contract.functions.totalUnderlyingWithFeesAndLeftOver(address_vault).call()

        amount0 = Decimal(results[0]) / Decimal(1000000)
        amount1 = Decimal(results[1]) / Decimal(1000000000000000000)
        fee0 = Decimal(results[2]) / Decimal(1000000)
        fee1 = Decimal(results[3]) / Decimal(1000000000000000000)
        leftOver0 = Decimal(results[4]) / Decimal(1000000)
        leftOver1 = Decimal(results[5]) / Decimal(1000000000000000000)
        metrics_update_dictionary = {
            'date':str(datetime.now()),
            'amount0': str(amount0),
            'amount1': str(amount1),
            'fee0': str(fee0),
            'fee1': str(fee1),
            'leftOver0': str(leftOver0),
            'leftOver1': str(leftOver1)
        }
        payload_message = json.dumps(metrics_update_dictionary)
        payload_message = payload_message.replace('"', '')
        payload_message = 'Production smart liquidity metrics : ' + payload_message
        send_slack_message(payload_message, incoming_web_hook=self.slack_hook)

        return amount0, amount1, fee0, fee1, leftOver0, leftOver1