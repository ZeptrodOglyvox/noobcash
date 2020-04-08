import click
import sys
import requests
from flask import request,jsonify
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
    ctx.obj['bootstrap_url'] = "http://127.0.0.1:5000" #"http://10.0.0.1:5000"
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
    ctx.obj['myurl'] = response.json()["address"]
    
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
            # ctx.obj['myurl'] = info.json()["address"]
            ctx.obj['myid'] = info.json()["node_id"] 
            ctx.obj['my_pkey'] = info.json()["public_key"]
            click.echo(response.json()["message"])

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
        ctx.obj['my_pkey'] = response.json()["public_key"]

@cli.command("register")
@click.pass_context
def register_node(ctx):
    """ This will add the current node (myurl) to other nodes' 
    peers list. The backend `/register_node` endpoint is called """

    url = ctx.obj['myurl'] + '/register'
    data = {
        'bootstrap_address': ctx.obj['bootstrap_url']
    }
    response = requests.post(url=url, json=data)
    if response.status_code == 400:
        click.echo("{}".format(response.json()["message"]))
    else:
        click.echo("{}".format(response.json()["message"]))
        ctx.obj['myid'] = response.json()["node_id"]



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
            click.echo("{}".format(response.json()["message"]))
        else:
            click.echo("Make sure all nodes are registered before calling net-setup.")
            click.echo("So far, {} nodes are registered, including bootstrap.".format(len(network)))


@cli.command("t")
@click.pass_context
@click.argument('recipient_id') 
@click.argument('amount')
def  new_transaction(ctx, recipient_id, amount):
    """ Sends <recipient_id>'s wallet 
    <amount> NBCs.  """
    # get_info to match id to ip address
    info = requests.get(url=ctx.obj['myurl'] + '/get_info')
    recipient_address = info.json()['network'][int(recipient_id)]['public_key']
    
    url = ctx.obj['myurl'] + '/transactions'
    data = dict(
       sender_address=ctx.obj['my_pkey'],
       recipient_address=recipient_address,
       amount=int(amount) 
    )
    response = requests.post(url=url+'/create',json=data)
    if response.status_code != 200:
        # error
        click.echo("{}".format(response.json()['message']))
    else:
        # or content or text or whatever?
        new_tx_dict = response.json() 
        sign_url = url + '/sign'
        resp = requests.post(url=sign_url, json=new_tx_dict)
        if resp.status_code != 200:
            click.echo("{}".format(resp.json()['message']))
        else:
            sgn =resp.json()['signature']
            submit_url = url + '/submit?broadcast=1'
            res = requests.post(url=submit_url, json={
                'transaction': new_tx_dict,
                'signature' : sgn
            })
            # 400 : Improper transaction JSON given
            #       Transaction validation failed
            #       Invalid signature 
            # 202 : Rejected by network
            # 200 : Transaction added to this BCs uncocnfirmed list
            click.echo("{}".format(res.json()['message']))

    # Now check if there are blocks to be mined.
    # If yes, mine them and broadcast them etc.
    url = ctx.obj['myurl'] + '/blockchain/get_capacity'    
    response = requests.get(url=url)
    capacity = response.json()['capacity']
    click.echo("unconfirmed: {}".format(capacity))

@cli.command("do-all-t")
@click.pass_context
def do_all_transactions(ctx):    
    for transaction in ctx.obj['transactions']:
        ctx.invoke(new_transaction, recipient_id=transaction[0], amount=transaction[1])


@cli.command("view")
@click.pass_context
def view_last_block_transactions(ctx):
    """ View last block's transactions. """
    url = ctx.obj['myurl'] + '/blockchain/get_last_block'
    response = requests.get(url=url)
    if response.status_code == 200:
        transactions_dict = response.json()['transactions']
        for entry in transactions_dict:
            click.echo('-- -- -- Transaction Begin -- -- --')
            click.echo("Tid: {}".format(entry['transaction_id']))
            click.echo("Sender: {}".format(entry['sender_address']))
            click.echo("Recipient: {}".format(entry["recipient_address"]))
            click.echo("Amount: {} NBCs".format(entry["amount"]))
            click.echo("-- -- --  Transaction End  -- -- --\n")
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
    click.echo("Node{} remaining balance: {} NBCs.".format(myid, balance))

@cli.command("info")
@click.pass_context
def show_info(ctx):
    url = ctx.obj['myurl'] + '/get_info'
    response = requests.get(url=url)
    network = response.json()['network']
    for entry in network:
        click.echo("--------")
        click.echo("{}\n".format(entry))
# @cli.command("help")
# @click.pass_context
# def print_help(ctx):
#     # ct = click.get_current_context()
#     click.echo(ctx.get_help())
#     ctx.exit()

def start():
    cli(obj={})         

if __name__ == '__main__':
    start()