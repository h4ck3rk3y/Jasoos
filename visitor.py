import ast

class RecursiveVisitor(ast.NodeVisitor):

    report = []
    filename = ''
    usual_suspects = set(['password', 'pass', 'secret', 'token', 'key', 'passwd', 'pwd'])
    fun_module = {}

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
    }

    bad_calls = {
        'pickle': {'functions' : ['loads', 'load', 'Unpickler'], 'severity': 'medium', 'text':'possible security issue with pickle'},
        'cPickle': {'functions' : ['loads', 'load', 'Unpickler'], 'severity': 'medium', 'text':'possible security issue with pickle'},
        'hashlib': {'functions' : ['md5'], 'severity': 'medium', 'text':'md-5 can be cracked, use something stronger'},
        'Crypto.Hash': {'functions':['MD2', 'MD4', 'MD5'], 'severity': 'medium','text':'md-5 can be cracked, use something stronger'},
        'cryptography.hazmat.primitives.hashes': {'functions': ['MD5'], 'severity': 'medium', 'text':'md-5 can be cracked use something stronger'},
        'marshal': {'functions': ['loads', 'load'], 'severity': 'medium', 'text': 'deserialization with marshall is dangerous'},
        'Crypto.Cipher': {'functions': ['ARC2','ARC4', 'Blowfish', 'DES', 'XOR'], 'severity': 'High', 'text': 'use AES insted'},
        ''
    }


    def recursive(func):
        def wrapper(self, node):
            func(self, node)
            for child in ast.iter_child_nodes(node):
                self.visit(child)

        return wrapper

    def set_filename(self, filename):
        self.filename = filename

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

        for target in node.targets:
            if isinstance(target, ast.Name) and target.id in self.usual_suspects:
                self.add_to_report('exposed-credentials', target.lineno, 'medium', 'low', 'assigned value to %s' %(target.id))

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
        lineno = node.lineno
        for alias in ast.iter_child_nodes(node):
            if isinstance(alias, ast.alias) and alias.name in self.bad_imports:
                self.add_to_report('bad-import', node.lineno, self.bad_imports[alias.name]['severity'], 'high', self.bad_imports[alias.name]['text'])

    @recursive
    def visit_ImportFrom(self, node):

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
                self.add_to_report('bad-import', node.lineno, self.bad_imports[alias.name]['severity'], 'high', self.bad_imports[alias.name]['text'])


    @recursive
    def visit_Call(self, node):

        if isinstance(node.func, ast.Name):
            #bad imports
            if node.func.id == '__import__' and len(node.args) > 0:
                module_name = node.args[0]
                if isinstance(module_name, ast.Str) and module_name.s in self.bad_imports:
                    self.add_to_report('bad-import', node.lineno, self.bad_imports[module_name.s]['severity'], 'high', self.bad_imports[module_name.s]['text'])

            #jinja-2-xss
            if node.func.id == 'Environment' and (self.fun_module.get(node.func.id, {}).get('module', None) == 'jinja2' and self.fun_module[node.func.id]['name'] == 'Environment'):
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

            # flask debug
            if getattr(node.func.value, 'id', None) == 'app' and node.func.attr == 'run':
                for keyword in node.keywords:
                    if keyword.arg=='debug' and keyword.value.id=='True':
                        self.add_to_report('debug-enabled', node.lineno, 'medium', 'high', 'running an application with debug enabled can be dangerous')

            # jinja-2-xss
            if getattr(node.func.value, 'id', None) == 'jinja2' and node.func.attr == 'Environment':
                auto_escape_found=False
                for keyword in node.keywords:
                    if keyword.arg=='autoescape' and (getattr(keyword.value, 'id', None)=='False' or getattr(keyword.value, 'value', None) == False):
                        self.add_to_report('xss', node.lineno, 'high', 'high', 'auto escape is set to False, please correct it or face XSS')
                        auto_escape_found = True
                    elif keyword.arg == 'autoescape':
                        auto_escape_found = True

                if not auto_escape_found:
                    self.add_to_report('xss', node.lineno, 'high', 'high', 'auto escape is false by default set to true, please correct it or face XSS')



    @recursive
    def visit_Module(self, node):
        pass



    @recursive
    def generic_visit(self, node):
        # print node,

        # try:
        #     print node.lineno
        # except:
        #     print

        pass