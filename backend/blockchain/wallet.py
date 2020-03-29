import Crypto
import Crypto.Random
from Crypto.PublicKey import RSA
import backend as node


class Wallet:
	def __init__(self):
		random_gen = Crypto.Random.new().read
		self.private_key = RSA.generate(1024, random_gen)
		self.public_key = self.private_key.publickey()

	@staticmethod
	def balance():
		# TODO: Figure out all the crypto library shiet, probably using strings
		#  for everything b. pubkey is also an address
		raise NotImplementedError
