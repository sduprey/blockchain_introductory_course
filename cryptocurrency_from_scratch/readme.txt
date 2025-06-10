#### Interact with PostMan
######## Launching nodes
#Launch Blockchain on port 5000 on console 0
GET
http://127.0.0.1:5000/get_chain
#Launch node 5001 on console 1
GET
http://127.0.0.1:5001/get_chain
#Launch node 5002 on console 2
GET
http://127.0.0.1:5002/get_chain
#Launch node 5003 on console 3
GET
http://127.0.0.1:5003/get_chain

######## Connecting the nodes together
http://127.0.0.1:5001/connect_node
{
    "nodes": ["http://127.0.0.1:5002",
              "http://127.0.0.1:5003"]
}
http://127.0.0.1:5002/connect_node
{
    "nodes": ["http://127.0.0.1:5001",
              "http://127.0.0.1:5003"]
}`
http://127.0.0.1:5003/connect_node
{
    "nodes": ["http://127.0.0.1:5002",
              "http://127.0.0.1:5003"]
}

######## Testing the consensus
##Mining a block
GET
http://127.0.0.1:5001/mine_block
## check the chains in the other nodes
GET
http://127.0.0.1:5001/get_chain
GET
http://127.0.0.1:5002/get_chain
GET
http://127.0.0.1:5003/get_chain
## Replace the chain
GET
http://127.0.0.1:5001/replace_chain
GET
http://127.0.0.1:5002/replace_chain
GET
http://127.0.0.1:5003/replace_chain

#### Adding a transaction
POST
http://127.0.0.1:5001/add_transaction
{
    "sender": "stefan",
    "receiver": "yannick",
    "amount": 1
}
##Mining a block
GET
http://127.0.0.1:5001/mine_block

## Replace the chain
GET
http://127.0.0.1:5001/replace_chain
GET
http://127.0.0.1:5002/replace_chain
GET
http://127.0.0.1:5003/replace_chain

#### Adding a transaction
POST
http://127.0.0.1:5002/add_transaction
{
    "sender": "me",
    "receiver": "you",
    "amount": 100
}
GET
http://127.0.0.1:5002/mine_block
## Replace the chain
GET
http://127.0.0.1:5001/replace_chain
GET
http://127.0.0.1:5002/replace_chain
GET
http://127.0.0.1:5003/replace_chain


#### And so on




##### advanced MIT projects
https://github.com/anders94/blockchain-demo/

https://tools.superdatascience.com/blockchain/hash/
https://tools.superdatascience.com/blockchain/hash
https://tools.superdatascience.com/blockchain/public-private-keys/keys
https://tools.superdatascience.com/blockchain/public-private-keys/signatures
https://tools.superdatascience.com/blockchain/blockchainhttps://tools.superdatascience.com/blockchain/distributed
https://tools.superdatascience.com/blockchain/tokens
