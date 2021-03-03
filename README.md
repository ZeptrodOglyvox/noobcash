A simple blockchain /cryptocurrency distributed application for our Distributed Systems class.


To install all requirements run

`python -m pip install -r requirements.txt`

To run most of the tests you need to manually run at least 3 instances of the flask server on the url 
`127.0.0.1:<port>` with `<port>` being an ascending number starting from 5000 (the bootstrap node port). 
With PyCharm this can be done using the Multirun plugin and setting up multiple flask server configurations
setting the environment variable FLASK_RUN_PORT. Manually this can be done by setting the FLASK_APP env variable 
(FLASK_APP=/backend/\__init\__.py)
and then running
 
 `flask run --host 127.0.0.1 --port <port>`
 
 on multiple terminals.
 
To use the CLI:
1. python3.7 cli.py --n <number of clients> --port <port> --bn (master?1:0)
2. * If this node is the bootstrap(master node) :
     ```>> boot-setup```
   * If this is just a client node :
     ~~~~
     >> generate-wallet
     >> register 
     ~~~~     
3. On master node:
    ``` >> net-setup```
4. On all nodes:
    ``` >> read-tx```
5. On all nodes:
    ```>> do-all-t```
