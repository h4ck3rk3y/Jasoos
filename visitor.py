import ast


# @ToDo
# Add Support for
# import A.B
# A.B.C.d()
# support such bad calls

class RecursiveVisitor(ast.NodeVisitor):

    report = []
    filename = ''
    usual_suspects = set(['password', 'pass', 'secret', 'token', 'passwd', 'pwd'])
    fun_module = {}

    # specifically for SQL injection, dumb way to make strings come together :/
    done_line = set()

    bad_imports = {
        'telnetlib': {'severity': 'high', 'text': 'Use SSH or some other encrypted protocol.'},
        'ftplib': {'severity': 'high', 'text': 'Use SSH/SFTP/SCP or some other encrypted protocol.'},
        'pickle': {'severity': 'low', 'text': 'possible security issues with pickle'},
        'cPickle': {'severity': 'low', 'text': 'possible security isses with cPickle'},
        'subprocess': {'severity': 'low', 'text': 'possible security isses with subprocess'},
        'xmlrpclib': {'severity': 'high', 'text': 'Use defused.xmlrpc.monkey_patch() function to monkey-patch xmlrpclib and mitigate remote XML attacks.'},
        'wsgiref.handlers.CGIHandler': {'severity': 'high', 'text': 'avoid use of cgi'},
        'twisted.web.twcgi.CGIScript': {'severity': 'high', 'text': 'avoid use of cgi'},
        'lxml': {'severity': 'low', 'text': 'use defused xml instead'},
        'xml.dom.pulldom': {'severity': 'low', 'text': 'use defusedxml instead'},
        'xml.dom.minidom': {'severity': 'low', 'text': 'use defusedxml instead'},
        'xml.dom.expatbuilder': {'severity': 'low', 'text': 'use defusedxml instead'},
        'xml.sax': {'severity': 'low', 'text': 'use defusedxml instead'},
        'xml.etree.ElementTree': {'severity': 'low', 'text': 'use defusedxml instead'},
        'xml.etree.cElementTree': {'severity': 'low', 'text': 'use defusedxml instead'},
        'mako': {'severity': 'medium', 'text': 'mako has no autoescape feature, use proper tags in html', 'heading': 'xss'},
        'mako.template': {'severity': 'medium', 'text': 'mako has no autoescape feature, use proper tags in html', 'heading': 'xss'},
    }

    # @ToDo
    # Add specific functions like new
    bad_calls = {
        'pickle': {'functions' : ['loads', 'load', 'Unpickler'], 'severity': 'medium', 'text':'possible security issue with pickle'},
        'cPickle': {'functions' : ['loads', 'load', 'Unpickler'], 'severity': 'medium', 'text':'possible security issue with pickle'},
        'hashlib': {'functions' : ['md5'], 'severity': 'medium', 'text':'md-5 can be cracked, use something stronger'},
        'Crypto.Hash': {'functions':['MD2.new', 'MD4.new', 'MD5.new'], 'severity': 'medium','text':'md-5 can be cracked, use something stronger'},
        'cryptography.hazmat.primitives.hashes': {'functions': ['MD5'], 'severity': 'medium', 'text':'md-5 can be cracked use something stronger'},
        'marshal': {'functions': ['loads', 'load'], 'severity': 'medium', 'text': 'deserialization with marshall is dangerous'},
        'Crypto.Cipher': {'functions': ['ARC2.new','ARC4.new', 'Blowfish.new', 'DES.new', 'XOR.new'], 'severity': 'High', 'text': 'use AES insted'},
        'cryptography.hazmat.primitives.ciphers': {'functions': ['algorithms.ARC4', 'algorithms.BlowFish', 'algorithms.IDEA'], 'severity': 'HIGH', 'text': 'use AES insted'},
        'cryptography.hazmat.primitives.ciphers.modes': {'functions': ['ECB'], 'severity': 'Medium', 'text': 'ECB has patterns use CBC instead?'},
        'tempfile': {'functions': ['mktemp_q'], 'severity': 'medium', 'text': 'the function is insecure and deprecated'},
        'django.utils.safestring.': {'functions': ['mark_safe'], 'severity': 'medium', 'text': 'possible xss, avoid using?'},
        'httplib': {'functions': ['HTTPSConnection'], 'severity': 'medium', 'text': 'use of HTTPSConnection doesnt provide safety'},
        'http.client': {'functions': ['HTTPSConnection'], 'severity': 'medium', 'text': 'use of HTTPSConnection doesnt provide safety'},
        'six.moves.http_client': {'functions': ['HTTPSConnection'], 'severity': 'medium', 'text': 'use of HTTPSConnection doesnt provide safety'},
        'random': {'functions': ['random', 'randrange', 'choice', 'uniform', 'triangular'], 'severity': 'low', 'text': 'not suitable for crypto purposes'},
        'paramiko': {'functions': ['exec_command'], 'severity': 'medium', 'text':'Possible shell injection via Paramiko call, check inputs are properly sanitized', 'heading': 'shell-injection'},
        'SSHClient': {'functions': ['invoke_shell'], 'severity': 'medium', 'text':'Possible shell injection, check inputs are properly sanitized', 'heading': 'shell-injection'},
        'os': {'functions': ['system', 'popen', 'popen2', 'popen3', 'popen4'], 'severity': 'low', 'text': 'Possible shell injection', 'heading': 'shell-injection'},
        'popen2': {'functions': ['popen2', 'popen3', 'popen4', 'Popen3', 'Popen4'], 'severity': 'low', 'text': 'Possible shell injection', 'heading': 'shell-injection'},
        'commands': {'functions': ['getoutput', 'getstatusoutput'], 'severity': 'low', 'text': 'Possible shell injection', 'heading': 'shell-injection'},
        'subprocess': {'functions': ['Popen', 'call', 'check_call', 'check_output'], 'severity': 'low', 'text': 'Possible shell injection', 'heading': 'shell-injection'}
    }

    bad_functions = [x['functions'] for x in bad_calls.values()]
    bad_functions = set([j for i in bad_functions for j in i])

    only_password = False

    def clear(self):
        self.report = []
        self.done_line = set()

    def recursive(func):
        def wrapper(self, node):
            response = func(self, node)
            if response is not False:
                for child in ast.iter_child_nodes(node):
                    self.visit(child)

        return wrapper

    def set_filename(self, filename):
        self.filename = filename

    def set_only_password(self, only_password):
        self.only_password = only_password

    def add_to_report(self, issue, location, severity, confidence, text):

        threat = {
            'issue': issue,
            'location': '%s: %d'%(self.filename, location),
            'severity': severity,
            'confidence': confidence,
            'text': text
        }

        self.report.append(threat)

    @recursive
    def visit_Assign(self, node):

        # direct assignment
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id in self.usual_suspects:
                self.add_to_report('exposed-credentials', target.lineno, 'medium', 'low', 'assigned value to %s' %(target.id))

        # dictionary
        if isinstance(node.value, ast.Str):
            for child_assign in ast.iter_child_nodes(node):
                if isinstance(child_assign, ast.Subscript):
                    for child_index in ast.iter_child_nodes(child_assign):
                        if isinstance(child_index, ast.Index):
                            for child_string in ast.iter_child_nodes(child_index):
                                if child_string.s in self.usual_suspects:
                                    self.add_to_report('exposed-credentials', child_string.lineno, 'medium', 'low', 'assigned value to dic index %s' %(child_string.s))
    @recursive
    def visit_Compare(self, node):
        if isinstance(node.left, ast.Name) and node.left.id in self.usual_suspects:
            if isinstance(node.comparators[0], ast.Str):
                self.add_to_report('exposed-credentials', node.lineno, 'medium', 'low', '%s compared with plain text' %(node.left.id))

    @recursive
    def visit_arguments(self, node):

        interesting_name = False
        argument = None

        for child in ast.iter_child_nodes(node):

            if interesting_name and isinstance(child, ast.Str):
                self.add_to_report('exposed-credentials', child.lineno, 'medium', 'low', 'argument %s given default value'%(argument))

            if isinstance(child, ast.Name) and child.id in self.usual_suspects:
                interesting_name = True
                argument = child.id
            else:
                interesting_name = False

    def visit_keyword(self, node):
        if node.arg in self.usual_suspects:
            self.add_to_report('exposed-credentials', node.value.lineno, 'medium', 'low', 'argument %s given value'%(node.arg))

    @recursive
    def visit_Import(self, node):

        if self.only_password:
            return

        lineno = node.lineno
        for alias in ast.iter_child_nodes(node):
            if alias.asname:
                self.fun_module[alias.asname] = {'module': alias.name, 'name': alias.name}
            else:
                self.fun_module[alias.name] = {'module': alias.name, 'name': alias.name}

            if isinstance(alias, ast.alias) and alias.name in self.bad_imports:
                heading = self.bad_imports[alias.name].get('heading', False) or 'bad-import'
                self.add_to_report(heading, node.lineno, self.bad_imports[alias.name]['severity'], 'high', self.bad_imports[alias.name]['text'])

    @recursive
    def visit_ImportFrom(self, node):

        if self.only_password:
            return

        lineno = node.lineno
        if node.module in self.bad_imports:
            self.add_to_report('bad-import', node.lineno, self.bad_imports[node.module]['severity'], 'high', self.bad_imports[node.module]['text'])

        for alias in ast.iter_child_nodes(node):
            if isinstance(alias, ast.alias):
                if alias.asname:
                    self.fun_module[alias.asname] = {'module': node.module, 'name': alias.name}
                else:
                    self.fun_module[alias.name] = {'module': node.module, 'name': alias.name}

            if isinstance(alias, ast.alias) and alias.name in self.bad_imports:
                heading = self.bad_imports[alias.name].get('heading', False) or 'bad-import'
                self.add_to_report(heading, node.lineno, self.bad_imports[alias.name]['severity'], 'high', self.bad_imports[alias.name]['text'])

    @recursive
    def visit_Call(self, node):

        if self.only_password:
            return

        if isinstance(node.func, ast.Name):

            # bad_calls direct
            module = self.fun_module.get(node.func.id, {}).get('module', None) or getattr(node.func, 'id' , False)
            if module in self.bad_calls and self.fun_module[node.func.id]['name'] in self.bad_functions:
                heading = self.bad_calls[module].get('heading', 'bad-calls')
                self.add_to_report(heading, node.lineno, self.bad_calls[module]['severity'], 'high', self.bad_calls[module]['text'])

            #bad imports
            if node.func.id == '__import__' and len(node.args) > 0:
                module_name = node.args[0]
                if isinstance(module_name, ast.Str) and module_name.s in self.bad_imports:
                    heading = self.bad_imports[module_name.s].get('heading', False) or 'bad-import'
                    self.add_to_report('bad-import', node.lineno, self.bad_imports[module_name.s]['severity'], 'high', self.bad_imports[module_name.s]['text'])

            #jinja-2-xss
            if (self.fun_module.get(node.func.id, {}).get('module', None) == 'jinja2' and self.fun_module[node.func.id]['name'] == 'Environment'):
                auto_escape_found=False
                for keyword in node.keywords:
                    if keyword.arg=='autoescape' and (getattr(keyword.value, 'id', None)=='False' or getattr(keyword.value, 'value', None) == False):
                        self.add_to_report('xss', node.lineno, 'high', 'high', 'auto escape is set to False, please correct it or face XSS')
                        auto_escape_found = True
                    elif keyword.arg == 'autoescape':
                        auto_escape_found = True


                if not auto_escape_found:
                    self.add_to_report('xss', node.lineno, 'high', 'high', 'auto escape is false by default set to true, please correct it or face XSS')


        if isinstance(node.func, ast.Attribute):

            # bad-calls
            # handles as imports properly
            module = self.fun_module.get(getattr(node.func.value, 'id', None), {}).get('module', None) or getattr(node.func.value, 'id', False)
            if module in self.bad_calls and (node.func.attr in self.bad_functions or (str(self.fun_module[node.func.value.id]['name']) + '.' +  str(node.func.attr)) in self.bad_functions):
                heading = self.bad_calls[module].get('heading', 'bad-calls')
                self.add_to_report(heading, node.lineno, self.bad_calls[module]['severity'], 'high', self.bad_calls[module]['text'])

            # flask debug
            if getattr(node.func.value, 'id', None) == 'app' and node.func.attr == 'run':
                for keyword in node.keywords:
                    if keyword.arg=='debug' and keyword.value.id=='True':
                        self.add_to_report('debug-enabled', node.lineno, 'medium', 'high', 'running an application with debug enabled can be dangerous')

            # jinja-2-xss
            # new version takes care of as imports
            if self.fun_module.get(getattr(node.func.value, 'id', None), {}).get('module', None) == 'jinja2' and node.func.attr == 'Environment':
                auto_escape_found=False
                for keyword in node.keywords:
                    if keyword.arg=='autoescape' and (getattr(keyword.value, 'id', None)=='False' or getattr(keyword.value, 'value', None) == False):
                        self.add_to_report('xss', node.lineno, 'high', 'high', 'auto escape is set to False, please correct it or face XSS')
                        auto_escape_found = True
                    elif keyword.arg == 'autoescape':
                        auto_escape_found = True

                if not auto_escape_found:
                    self.add_to_report('xss', node.lineno, 'high', 'high', 'auto escape is false by default set to true, please correct it or face XSS')

            if node.func.attr in ('execute', 'executemany') and len(node.args)>1:
                return False

            #exec-as-root
            if (self.fun_module.get(getattr(node.func.value, 'id', None), {}).get('module', None) in ('ceilometer', 'cinder', 'neutron.agent.linux', 'nova') and self.fun_module[node.func.value.id]['name'] == 'utils'):
                for keyword in node.keywords:
                    if keyword.arg=='run_as_root' and (getattr(keyword.value, 'id', None)=='False' or getattr(keyword.value, 'value', None) == True):
                        self.add_to_report('exec-as-root', node.lineno, 'low', 'high', 'run as root can be potentially dangerous, set to false')
                        auto_escape_found = True

    @recursive
    def visit_BinOp(self, node):

        if self.only_password:
            return

        if node.lineno in self.done_line:
            return

        query = []
        left = node
        while isinstance(left, ast.BinOp):
            right = left.right
            if isinstance(right, ast.Str):
                query.append(right.s)
            left = left.left
        if isinstance(left, ast.Str):
            query.append(left.s)
        query = ' '.join(query[::-1]).replace('  ', '').lower()
        if not query:
            return
        injection = ((query.startswith('select ') and ' from ' in query) or
            query.startswith('insert into') or
            (query.startswith('update ') and ' set ' in query) or
            query.startswith('delete from '))

        self.add_to_report('sql-injection', node.lineno, 'medium', 'low', 'potential sqli by using string based queries')
        self.done_line.add(node.lineno)

    @recursive
    def visit_Module(self, node):
        pass

    @recursive
    def visit_Exec(self, node):
        if self.only_password:
            return

        self.add_to_report('exec-used', node.lineno, 'medium', 'high', 'use of exec is risky')

    @recursive
    def generic_visit(self, node):
        pass