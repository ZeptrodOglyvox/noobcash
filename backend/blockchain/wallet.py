import binascii

import Crypto
import Crypto.Random
from Crypto.PublicKey import RSA
import backend as node


class Wallet:
	def __init__(self):
		random_gen = Crypto.Random.new().read
		self.private_key_rsa = RSA.generate(1024, random_gen)
		self.public_key_rsa = self.private_key_rsa.publickey()

		self.private_key = binascii.hexlify(self.private_key_rsa.exportKey(format='DER')).decode('ascii')
		self.public_key = binascii.hexlify(self.public_key_rsa.exportKey(format='DER')).decode('ascii')
		self.address = self.public_key

	def balance(self):
		# TODO: Its pretty weird that the balance is calculated via utxos outside the object
		return sum(utxo.amount for utxo in node.utxos[self.address])

	# @property
	# def public_key_rsa(self):
	# 	return RSA.import_key(binascii.unhexlify(self.public_key))
	#
	# @property
	# def private_key_rsa(self):
	# 	return RSA.import_key(binascii.unhexlify(self.public_key))
