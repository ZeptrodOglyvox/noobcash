import binascii

import Crypto
import Crypto.Random
from Crypto.PublicKey import RSA
import backend as node


class Wallet:
	def __init__(self):
		random_gen = Crypto.Random.new().read
		private_key = RSA.generate(1024, random_gen)
		public_key = private_key.publickey()

		self.private_key = binascii.hexlify(private_key.exportKey(format='DER')).decode('ascii')
		self.public_key = binascii.hexlify(public_key.exportKey(format='DER')).decode('ascii')
		self.address = self.public_key

	def balance(self):
		return sum(utxo.amount for utxo in node.utxos[self.address])

	@property
	def public_key_rsa(self):
		return RSA.import_key(binascii.unhexlify(self.public_key))

	@property
	def private_key_rsa(self):
		return RSA.import_key(binascii.unhexlify(self.public_key))
