from dulwich import porcelain
from dulwich.errors import *

from urlparse import urlparse

import math

import ast
from visitor import RecursiveVisitor

import os
# ToDO
# Add something to lower the false positive tests. an option maybe.
# Add parts of code affected for front end?

class StaticAnalyzer:
	def __init__(self, url):
		self.url = url

		if not self.validate_url():
			raise Exception('Invalid URL')

		try:
			os.mkdir('repos')
		except:
			pass


		try:
			self.repo = porcelain.clone(self.url, self.path)
		except NotGitRepository:
			raise Exception('Not Git Repo')
		except OSError:
			raise Exception('File seems to have been already analyzed')

	def validate_url(self):
		parsed_url = urlparse(self.url)
		self.path = 'repos/%s' %(parsed_url.path[1:].replace('/', '-'))

		if not parsed_url.netloc == 'github.com':
			return False, "Host not GitHub"

		if parsed_url.scheme in ("https", "http"):
			self.url = self.url.replace('https', 'git').replace('http', 'git')
			return True

		if parsed_url.scheme == 'git':
			return True

	def run_tests(self, source, filename):
		tree = ast.parse(source)
		recursive_visitor = RecursiveVisitor()
		recursive_visitor.set_filename(filename)
		recursive_visitor.visit(tree)

	def analyze(self):

		for root, dirs, files in os.walk(self.path):
			for f in files:
				_, extension = os.path.splitext(f)[1]

				# maybe support other files in the future
				if extension not in ('.py'):
					continue

				with open(os.path.join(root, f), 'r').read() as source:
					self.run_tests(source, f)

