# Python Static Code Analyzer in a Python

A lot of the tests have been borrowed from the package 'bandit' by OpenStack.

I've implemented tests for a lot of things including

- XSS
- sqli
- exposed credentials
- shell injection
- dangerous functions
- dangerous imports
- debug enabled


# Installation Instructions

You need redis and twistd installed and running on your system for the application to run.

```

$ git clone https://gitlab.com/prezi-homeassignments/Assignment-Security-GyanendraMishra

$ pip install -r requirements.txt

$ ./start.sh

Visit http://localhost:8080

Profit??

```

# Usage

The static code analyzer uses the parses the AST of the source file.

You can view the web version here, it produces html output
- ec2-52-210-224-160.eu-west-1.compute.amazonaws.com

For JSON consume the api at

- ec2-52-210-224-160.eu-west-1.compute.amazonaws.com/api/analyzer

The API accepts post requests with 'url' set to a GitHub repository
it returns an object that contains an id which you will use to query
the result of the analysis

- ec2-52-210-224-160.eu-west-1.compute.amazonaws.com/api/result/:id

Replace :id with the id provided by the above API.


# Fixable shortcomings (could have used more time)

- Better Documentation
- The visitor and analyzer functions could be more extensible to use 'plugins' like repoguard has rules or how openstack has plugins. Some sort of extensibility has been achieved by the bad_imports and bad_calls dictionaries.
- Code could have been more robust and could have had tests
- A Better UI
- Support for other common web files like actual template files for checking things like {% autoescape off  %}
- Alert feature to schedule cron jobs to test the repository and mail developers
- A wider variety of issues could be covered
- Performance should be improved via threads or asynchronicity. The redis queue implementation is just a hack to make the UI fancy and the user not waiting.