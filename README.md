# Jasoos
## Python Static Code Analyzer in a Python

Jasoos means 'Detective' in Hindi.

A lot of the tests have been borrowed from the package 'bandit' by OpenStack.

I've implemented tests for a lot of things including

- XSS
- sqli
- exposed credentials
- shell injection
- dangerous functions
- dangerous imports
- debug enabled
- csrf


# Installation Instructions

You need redis and twistd installed and running on your system for the application to run.

```

$ git clone https://github.com/h4ck3rk3y/Jasoos

$ pip install -r requirements.txt

$ ./start.sh

Visit http://localhost:8080

Profit??

```

# Usage

The static code analyzer uses the parses the AST of the source file.

You can view the web version here, it produces html output
- localhost:8080

For JSON consume the api at

- localhost:8080/api/analyzer

The API accepts post requests with 'url' set to a GitHub repository
it returns an object that contains an id which you will use to query
the result of the analysis

- localhost:8080/api/result/:id

Replace :id with the id provided by the above API.


# Fixable shortcomings

- Better Documentation
- The visitor and analyzer functions could be more extensible to use 'plugins' like repoguard has rules or how openstack has plugins. Some sort of extensibility has been achieved by the bad_imports and bad_calls dictionaries.
- Code could have been more robust and could have had tests
- A Better UI
- Support for other common web files like actual template files for checking things like {% autoescape off  %}
- Alert feature to schedule cron jobs to test the repository and mail developers
- A wider variety of issues could be covered
- Performance could be improved by better implementations or scanning methods.
- Look for credentials in deleted files. A keys.py might have been committed earlier by the developer. He might have tried to git rm it to fix it, but it's always there anyway.