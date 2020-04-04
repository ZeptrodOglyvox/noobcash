import click
import sys
import requests
from flask import request
import json
# pip install click-shell
from click_shell import shell

# TODO: replace all response.content with response.json()
# assume clients will run at ports 5000 and 5001 of PCs
# TODO: match public keys to ids in create_transaction ("t")

# bootstrap_node will be PC0:5000
# bootstrap_url = "http://10.0.0.1:5000"
# my_pkey = ""
# n_clients = 5
# myurl = "http://127.0.0.1"
# is_bootstrap = False
# myid = 0

# Each node/client will have this list of transactions
# new transactions to perform will be picked from this
# list and then removed 

# @click.group() no more
@shell(prompt='cli >> ', intro='Starting up node...')
@click.pass_context
@click.option('--bn', default=False, \
    help='True if this is going to be the bootstrap node')
@click.option('--n', default=5,help='Number of clients')
@click.option('--host', default='http://127.0.0.1')
@click.option('--port', default='5000')
def cli(ctx, bn: bool = False, n: int = 5, \
    host: str = "http://127.0.0.1", port: str = "5000"):
    ctx.obj['is_bootstrap'] = bool(bn)
    ctx.obj['n_clients'] = int(n)
    ctx.obj['myurl'] = host + ":" + port
    ctx.obj['bootstrap_url'] = "http://10.0.0.1:5000"
    ctx.obj['transactions'] = []
    if ctx.obj['is_bootstrap']:
        ctx.obj['myid'] = 0    
    else:
        ctx.obj['myid'] = -1
    ctx.obj['my_pkey'] = ""
    click.echo(ctx.obj['is_bootstrap'])
    click.echo(ctx.obj['n_clients'])
    click.echo(ctx.obj['myurl'])
    click.echo(ctx.obj['bootstrap_url'])
 

@cli.command("read-tx")
@click.pass_context
def read_transactions(ctx):
    """ Once all nodes are registered, read the transactions to be 
    perorfmed from a txt file and store them in local list.
    """ 
    filename = "transactions" + str(ctx.obj['myid']) + ".txt"
    # get matching of node-ids to addresses from respective endpoint
    url = ctx.obj['myurl'] + '/get_info'
    response = requests.get(url=url)
    # update it? not sure if it should be the loopback
    # or our intnet address
    ctx.obj['myurl'] = response.content["address"]
    
    with open(filename) as f:
        for line in f:
            node_id = int(line.split()[0][-1])
            amount = int(line.split()[1])
            ctx.obj['transactions'].append((node_id, amount))
    
    click.echo(ctx.obj['transactions'][:10])
    

@cli.command("boot-setup")
@click.pass_context
def setup_bootstrap(ctx):
    if not ctx.obj['is_bootstrap']:
        click.echo("This is not the bootstrap node!\
        You should run wallet instead!")
    else:
        amount = 100*ctx.obj['n_clients']
        url = ctx.obj['bootstrap_url'] + '/setup_bootstrap'
        data = {
            'initial_amount' : amount
        }
        response = requests.post(url=url, json=data)
        if response.status_code == 200:
            info_url = ctx.obj['myurl']+'/get_info'
            info = requests.get(url=info_url)
            # ctx.obj['myurl'] = info.content["address"]
            ctx.obj['myid'] = info.content["node_id"] 
            ctx.obj['my_pkey'] = info.content["public_key"]
            click.echo(response.content["message"])

@cli.command("generate-wallet")
@click.pass_context
def generate_wallet(ctx):
    """ 
    Generate a wallet for this node. (Not for the bootstrap).
    Call it before you begin transacting.
    """
    url = ctx.obj["myurl"] + '/generate_wallet'
    response = requests.get(url=url)
    if response.status_code == 200:
        ctx.obj['my_pkey'] = response.content["public_key"]

@cli.command("register")
@click.pass_context
def register_node(ctx):
    """ This will add the current node (myurl) to other nodes' 
    peers list. The backend `/register_node` endpoint is called """

    url = ctx.obj['myurl'] + '/register'
    data = {
        'bootstrap_address': ctx.obj['bootstrap_url']
    }
    response = requests.post(url=url, data=data)
    if response.status_code == 400:
        click.echo("{}".format(response.content["message"]))
    else:
        click.echo("{}".format(response.content["message"]))
        ctx.obj['myid'] = response.content["node_id"]



@cli.command("net-setup") 
@click.pass_context
def setup_network(ctx):
    """ Calls /setup_network endpoint to send each registered node
    a copy of the current blockchain and current network"""
    if not ctx.obj['is_bootstrap']:
        click.echo("This function is only called \
            from the bootstrap node.")
    else:
        # make a request to get the length of the network
        resp = requests.get(ctx.obj['bootstrap_url']+'/get_info')
        network = resp.json()["network"]
        if len(network) == ctx.obj['n_clients']:
            url = ctx.obj['bootstrap_url'] + '/setup_network'
            response = requests.get(url=url)
            click.echo("{}".format(response.content["message"]))
        else:
            click.echo("Make sure all nodes are registered before calling net-setup.\n")
            click.echo("So far, {} nodes are registered, including bootstrap.".format(len(network)))


@cli.command("t")
@click.pass_context
@click.argument('recipient_address') 
@click.argument('amount')
def  new_transaction(ctx,recipient_address, amount):
    """ Sends <recipient_address>'s wallet 
    <amount> NBCs.  """
    url = ctx.obj['myurl'] + '/transactions'
    data = dict(
       sender_address=ctx.obj['my_pkey'],
       recipient_address=recipient_address,
       amount=amount 
    )
    response = requests.post(url=url+'/create',data=data)
    if response.status_code != 200:
        # error
        click.echo("{}".format(response.json()['message']))
    else:
        # or content or text or whatever?
        new_tx_dict = response.json() 
        sign_url = url + '/sign'
        resp = requests.post(url=sign_url, data=new_tx_dict)
        if resp.status_code != 200:
            click.echo("{}".format(resp.json['message']))
        else:
            sgn =resp.json()['signature']
            submit_url = url + '/submit?broadcast=1'
            res = requests.post(url=submit_url, data={
                'transaction': new_tx_dict,
                'signature' : sgn
            })

@cli.command("view")
@click.pass_context
def view_last_block_transactions(ctx):
    """ View last block's transactions. """
    url = ctx.obj['myurl'] + '/blockchain/get_last_block'
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
@click.pass_context
def show_balance(ctx):
    """ Show node's current balance in NBCs."""
    url = ctx.obj['myurl'] + '/get_info'
    response = requests.get(url=url)
    balance = response.json()['balance']
    myid = response.json()['node_id']
    click.echo("Node{} remaining balance: {} NBCs\n.".format(myid, balance))

def start():
    cli(obj={})         

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


