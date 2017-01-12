from dulwich import porcelain
from dulwich.errors import *
from dulwich.repo import Repo
from dulwich.object_store import tree_lookup_path


from urlparse import urlparse

import math

import ast
from visitor import RecursiveVisitor

import os
import shutil

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
            raw_input
            self.repo = porcelain.clone(str(self.url), str(self.path))
        except NotGitRepository:
            shutil.rmtree(self.path)
            raise Exception('Not Git Repo')
        except OSError:
            shutil.rmtree(self.path)
            raise Exception('File seems to have been already analyzed')

        self.complete_report = {}

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

    def run_tests(self, source, filename, only_password = False, commit = 'HEAD'):
        tree = ast.parse(source)
        recursive_visitor = RecursiveVisitor()
        recursive_visitor.clear()
        recursive_visitor.set_filename(filename)
        recursive_visitor.set_only_password(only_password)
        recursive_visitor.visit(tree)
        if len(recursive_visitor.report) > 0:
            self.complete_report[filename] = self.complete_report.get(filename, {})
            self.complete_report[filename]['commits'] = self.complete_report[filename].get('commits', {})
            self.complete_report[filename]['commits'][commit]= recursive_visitor.report

    def get_file(self, r, tree, path):
        print tree, path
        (mode,sha) = tree_lookup_path(r.get_object,tree,path)
        return r[sha].data

    def analyze(self):

        # ToDo add support for older file versions
        for root, dirs, files in os.walk(self.path):
            for f in files:

                # maybe support other files in the future
                if not f.endswith('.py'):
                    continue

                with open(os.path.join(root, f), 'r') as source_file:
                    self.run_tests(source_file.read(), f)

        r = Repo(self.path)
        for root, dirs, files in os.walk(self.path):
            for f in files:

                if not f.endswith('.py'):
                    continue

                walker = r.get_walker(paths=[f])
                commits = iter(walker)

                first = True
                for commit in commits:
                    if first:
                        first = False
                        continue
                    source = self.get_file(r, r[commit.commit.id].tree, f)
                    self.run_tests(source, f, True, commit.commit.id)

        shutil.rmtree(self.path)