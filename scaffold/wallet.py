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
		self.public_key = private_key.publickey()
		self.address = None  # TODO: what should the address be?
		self.transactions = []

	def balance(self):
		raise NotImplementedError
