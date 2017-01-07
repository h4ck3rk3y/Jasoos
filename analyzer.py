from dulwich import porcelain
from dulwich.errors import *
from urlparse import urlparse
import math


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

		self.load_tests()
		self.analyze()

	def validate_url(self):
		parsed_url = urlparse(self.url)
		self.path = 'repos/%s' %(parsed_url.path[1:].replace('/', '-'))

		if not parsed_url.netloc == 'github.com':
			return False, "Host not GitHub"

		if parsed_url.scheme in ("https", "http"):
			self.url.replace('https', 'git').replace('http', 'git')
			return True

		if parsed_url.scheme == 'git':
			return True

	def add_to_report(self, issue, location, severity, confidence):

		threat = {
			'issue': issue
			'location': location,
			'severity': severity,
			'confidence': confidence
		}

		self.report.append(threat)


	def load_tests(self):
		self.codechecks = []
		for codechecker in os.listdir('codechecks'):
			self.codechecks.append('codechecks.%s' %(codechecker.replace('.py', '')))

	def analyze(self):
		self.report =  []


