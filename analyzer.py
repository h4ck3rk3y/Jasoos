from dulwich.repo import Repo
from dulwich.object_store import tree_lookup_path
from git import Repo as rp

import random
import string

from urlparse import urlparse

import math

import ast
from visitor import RecursiveVisitor

import os
import shutil

# @ToDO
# Add something to lower the false positive tests. an option maybe.
# Add parts of code affected for front end?

# Static Analyzer Class
class StaticAnalyzer:
    def __init__(self, url, previous, job):
        self.url = url

        if not self.validate_url():
            raise Exception('Invalid URL')

        try:
            os.mkdir('repos')
        except:
            pass


        try:
            rp.clone_from(self.url, self.path)
        except:
            self.job.meta['error'] = 'Couldnt clone repository'
            self.job.save()

        self.complete_report = {}
        self.job = job
        self.previous = previous

    # A function that performs basic validation of the URL
    def validate_url(self):
        parsed_url = urlparse(self.url)
        temp_path = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(35))
        self.path = 'repos/%s' %(temp_path)

        if not parsed_url.netloc == 'github.com':
            return False, "Host not GitHub"

        if parsed_url.scheme in ("https", "http"):
            self.url = self.url.replace('https', 'git').replace('http', 'git')
            return True

        if parsed_url.scheme == 'git':
            return True

    # A function that runs tests on the given file
    def run_tests(self, source, filename, only_password = False, commit = 'HEAD'):
        try:
            tree = ast.parse(source)
        except:
            self.complete_report[filename] = {'error': 'couldnt parse the source',
            'commit': commit}
            return
        recursive_visitor = RecursiveVisitor()
        recursive_visitor.clear()
        recursive_visitor.set_filename(filename)
        recursive_visitor.set_only_password(only_password)
        recursive_visitor.visit(tree)
        if len(recursive_visitor.report) > 0:
            self.complete_report[filename] = self.complete_report.get(filename, {})
            self.complete_report[filename]['commits'] = self.complete_report[filename].get('commits', {})
            self.complete_report[filename]['commits'][commit]= recursive_visitor.report

    # Fetches previous version of a given file
    def get_file(self, r, tree, path):
        (mode,sha) = tree_lookup_path(r.get_object,tree,path)
        return r[sha].data

    # reads through the repository for files
    # and calls run_tests on them
    def analyze(self):


        # ToDo add support for older file versions
        for root, dirs, files in os.walk(self.path):
            for f in files:

                # maybe support other files in the future
                if not f.endswith('.py'):
                    continue

                cleaned_path = os.path.join(root, f).replace(self.path, '')
                self.job.meta['current_file'] = cleaned_path
                self.job.save()

                with open(os.path.join(root, f), 'r') as source_file:
                    self.run_tests(source_file.read(), cleaned_path)

        if self.previous:
            try:
                r = Repo(self.path)
            except:
                return

            for root, dirs, files in os.walk(self.path):
                for f in files:

                    if not f.endswith('.py'):
                        continue

                    cleaned_path = os.path.join(root, f).replace(self.path, '')
                    self.job.meta['current_file'] = cleaned_path
                    self.job.save()

                    walker = r.get_walker(paths=[cleaned_path[1:]])
                    commits = iter(walker)

                    first = True
                    for commit in commits:
                        if first:
                            first = False
                            continue
                        try:
                            source = self.get_file(r, r[commit.commit.id].tree, cleaned_path[1:])
                            self.run_tests(source, cleaned_path, True, commit.commit.id)
                        except KeyError:
                            # known dulwich error
                            # @FixThis
                            pass
        shutil.rmtree(self.path)