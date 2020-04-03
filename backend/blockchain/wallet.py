import binascii

import Crypto
import Crypto.Random
from Crypto.PublicKey import RSA


class Wallet:
	def __init__(self):
		random_gen = Crypto.Random.new().read
		self.private_key_rsa = RSA.generate(1024, random_gen)
		self.public_key_rsa = self.private_key_rsa.publickey()

		self.private_key = binascii.hexlify(self.private_key_rsa.exportKey(format='DER')).decode('ascii')
		self.public_key = binascii.hexlify(self.public_key_rsa.exportKey(format='DER')).decode('ascii')
		self.address = self.public_key
