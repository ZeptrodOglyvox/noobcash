import click
import sys
import requests
from flask import request
import json
# pip install click-shell
from click_shell import shell
# import backend as node

# assume clients will run at ports 5000 and 5001 of PCs

# bootstrap_node will be PC0:5000
bootstrap_url = "http://10.0.0.1:5000"
my_pkey = ""
n_clients = 5
myurl = ""
is_bootstrap = False
myid = 0

# Each node/client will have this list of transactions
# new transactions to perform will be picked from this
# list and then removed 
transactions = []

# @click.group() no more
@shell(prompt='cli >> ', intro='Starting up node...')
@click.option('--bn', default=False, \
    help='True if this is going to be the bootstrap node')
@click.option('--n', default=5,help='Number of clients')
@click.option('--host', default='127.0.0.1')
@click.option('--port', default='5000')
def cli(bn: bool = False, n: int = 5, \
    host: str = "127.0.0.1", port: str = "5000"):
    is_bootstrap = bool(bn)
    n_clients = int(n)
    myurl = host + ":" + port
    click.echo(is_bootstrap)
    click.echo(n_clients)
    click.echo(myurl)
 

@cli.command("read-tx")
def read_transactions():
    """ Read the transactions to be perorfmed 
    from a txt file and store them in local list.
    """ 
    filename = "transactions" + str(myid) + ".txt"
    # myid = str(file).split('transactions')  
    # id = int(myid[1].split('.txt')[0])
    # click.echo(myid)
    # click.echo(id)
    with open(filename) as f:
        for line in f:
            node_id = int(line.split()[0][-1])
            amount = int(line.split()[1])
            transactions.append((node_id, amount))
    
    click.echo(transactions[:10])
    

@cli.command("boot-setup")
def setup_bootstrap():
    if not is_bootstrap:
        click.echo("This is not the bootstrap node!\
        You should run wallet instead!")
    else:
        amount = 100*n_clients
        url = bootstrap_url + '/setup_bootstrap'
        data = {
            'initial_amount' : amount
        }
        response = requests.post(url=url, json=data)
        if response.status_code == 200:
            if bootstrap_url == node.network[0]["ip"]:
                # It should be
                myurl = bootstrap_url
                myid = node.network[0]["id"]
                my_pkey = node.network[0]["public_key"]
                click.echo(response.content["message"])

@cli.command("wallet")
def generate_wallet():
    """ 
    Generate a wallet for this node. Call it before you
    begin transacting.
    """
    url = myurl + '/generate_wallet'
    response = requests.get(url=url)
    if response.status_code == 200:
        my_pkey = response.content["public_key"]

@cli.command("register")
def register_node():
    """ This will add the current node (myurl) to other nodes' 
    peers list. The backend `/register_node` endpoint is called """

    url = myurl + '/register'
    data = {
        'bootstrap_address': bootstrap_url
    }
    response = requests.post(url=url, data=data)
    if response.status_code == 400:
        click.echo("{}".format(response.content["message"]))
    else:
        click.echo("{}".format(response.content["message"]))
        myid = response.content["node_id"]
        node.node_id = myid


@cli.command("ready")
def check_all_nodes_registered():
    return len(node.network) == n_clients
    
@cli.command("net-setup")    
def setup_network():
    if not is_bootstrap:
        click.echo("This function is only called \
            from the bootstrap node.")
    else:
        url = bootstrap_url + '/setup_network'
        response = requests.get(url=url)
        if response.status_code == 200:
            click.echo("{}".format(response.content["message"]))


@cli.command("t")
@click.argument('recipient_address') 
@click.argument('amount')
def  new_transaction(recipient_address, amount):
    """ Sends <recipient_address>'s wallet 
    <amount> NBCs.  """
    pass

@cli.command("view")
def view_last_block_transactions():
    """ View last block's transactions. """
    url = myurl + '/blockchain/get_last_block'
    response = requests.get(url=url)
    if response.status_code == 200:
        transactions_dict = response.json()['transactions']
        for entry in transactions_dict:
            click.echo('-- -- -- Transaction Begin -- -- --\n')
            click.echo("Tid: {}\n".format(entry['transaction_id']))
            click.echo("Sender: {}\n".format(entry['sender_address']))
            click.echo("Recipient: {}\n".format(entry["recipient_address"]))
            click.echo("Amount: {} NBCs\n".format(entry["amount"]))
            click.echo("-- -- -- -- --\n")
    else:
        click.echo("Could not get last block transactions.\n")

@cli.command("balance")
def show_balance():
    """ Show node's current balance in NBCs."""
    balance = node.wallet.balance()
    click.echo("Node{} remaining balance: {} NBCs\n.".format(myid, balance))

def start():
    cli()         

if __name__ == '__main__':
    start()
    # 1.
    # update_peers()
    # 2.
    # make_bootstrap()
    # get_bootstrap()
    # read_transactions()  
    # 3. begin transacting
    # while transactions:
    #     new_tx = transactions.pop(0)
    #     recipient_address = node_url_dict[new_tx[0]]
    #     amount = new_tx[1]
    #     new_transaction(recipient_address, amount)


