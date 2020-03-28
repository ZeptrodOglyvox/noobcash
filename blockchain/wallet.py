import binascii

import Crypto
import Crypto.Random
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5

import hashlib
import json
from time import time
from urllib.parse import urlparse
from uuid import uuid4


class Wallet:
	def __init__(self):
		random_gen = Crypto.Random.new().read
		self.private_key = RSA.generate(1024, random_gen)
		self.public_key = self.private_key.publickey()
		self.utxos = []

	def balance(self):
		raise NotImplementedError
