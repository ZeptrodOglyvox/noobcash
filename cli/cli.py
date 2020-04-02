import click
import sys
import requests

# TODO : match address:port to node/client numbers
# Not sure if this matching is correct
# assume clients will run at ports 5000 and 5001 of PCs
node_url_dict = {'id0': "http://10.0.0.1:5000", 'id1': "http://10.0.0.2:5000",
                 'id2': "http://10.0.0.3:5000", 'id3': "http://10.0.0.4:5000",
                 'id4': "http://10.0.0.5:5000", 'id5': "http://10.0.0.1:5001",
                 'id6': "http://10.0.0.2:5001", 'id7': "http://10.0.0.3:5001",
                 'id8': "http://10.0.0.4:5001", 'id9': "http://10.0.0.5:5001"}

# Each node/client will have this list of transactions
# new transactions to perform will be picked from this
# list and then removed 
transactions = []



@click.command()
@click.argument('file', type=click.File('r'))
def read_transactions(file):
    """ Just read the transactions to be perorfmed 
    from a txt file and store them in local list. """    
    for line in file:
        node_id = line.split()[0]
        amount = int(line.split()[1])
        transactions.append((node_id, amount))
    
    click.echo(transactions[:10])

@click.command()
@click.argument('node_address') 
def register_node(node_address):
    """ this will add the node to other nodes' peers list
    The backend /register_node endpoint is called """
    # This will be called in main before anything else. Once all nodes 
    # have called it they can proceed with reading transactions.txt.
    # Note a reply (200 OK) means that the current node was 
    # registered in other nodes' peer list.
    # This node will have its own peers list updated when it receives 
    # requests from other nodes

    for client in node_url_dict.values:
        url = client
        data = {
            'node_address': node_address
        }
        response = requests.post(url=url, data=data)

@click.command("t")
@click.argument('recipient_address') 
@click.argument('amount')
def  new_transaction(recipient_address, amount):
    """ Sends <recipient_address>'s wallet 
    <amount> NBCs.  """


if __name__ == '__main__':
    # 1.
    # update_peers()
    # 2.
    read_transactions()  
    # 3. begin transacting


