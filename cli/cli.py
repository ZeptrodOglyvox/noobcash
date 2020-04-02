import click
import sys
import requests
from flask import request
import backend as node

# TODO : match address:port to node/client numbers
# Not sure if this matching is correct
# assume clients will run at ports 5000 and 5001 of PCs

# bootstrap_node will be PC0:5000
node_url_dict = {'id0': "http://10.0.0.1:5000"}

myurl = ""

# Each node/client will have this list of transactions
# new transactions to perform will be picked from this
# list and then removed 
transactions = []



@click.command()
@click.argument('file', type=click.File('r'))
def read_transactions(file):
    """ Read the transactions to be perorfmed 
    from a txt file and store them in local list.
    """ 

    myid = str(file).split('transactions')  
    id = 'id' + myid[1].split('.txt')[0]
    # click.echo(myid)
    # click.echo(id)
    myurl = node_url_dict[id]
    click.echo(myurl)
    for line in file:
        node_id = line.split()[0]
        amount = int(line.split()[1])
        transactions.append((node_id, amount))
    
    click.echo(transactions[:10])

@click.command()
@click.argument('node_address') 
def register_node(node_address):
    """ This will add the current node (myurl) to other nodes' (node_address) 
    peers list. The backend `/register_node` endpoint is called """
    # This will be called in main before anything else. Once all nodes 
    # have called it they can proceed with reading transactions.txt.
    # Note a reply (200 OK) means that the current node was 
    # registered in other nodes' peer list.
    # This node will have its own peers list updated when it receives 
    # requests from other nodes

    for client in node_url_dict.values:
        url = client + '/register_node'
        data = {
            'node_address': myurl
        }
        response = requests.post(url=url, data=data)

@click.command("t")
@click.argument('recipient_address') 
@click.argument('amount')
def  new_transaction(recipient_address, amount):
    """ Sends <recipient_address>'s wallet 
    <amount> NBCs.  """
    pass

@click.command("view")
def view_last_block_transactions():
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


         

if __name__ == '__main__':
    # 1.
    # update_peers()
    # 2.
    read_transactions()  
    # 3. begin transacting
    while transactions:
        new_tx = transactions.pop(0)
        recipient_address = node_url_dict[new_tx[0]]
        amount = new_tx[1]
        new_transaction(recipient_address, amount)


