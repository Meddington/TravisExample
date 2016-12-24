Rest Target Documentation
=========================

This is the primary target for examples provided in the Peach API Security
documentation and this SDK.

The rest target is a working example of a REST API backed by a SQLite database.
The example target contains one or more SQL injection vulnerabilities that can be 
identified by fuzzing the API.

For additional information regarding this example please see the
Peach API Security documentation.

This test target is built with the following stack:

 - Python
 - Flask
 - Flask RESTful
 - SQLite

Installation
------------

This target requires some Python modules to run.

----
pip install -r requirements.txt
----
 
Running
-------

Target runs with Python 2.7.

----
python rest_target.py
----

For SSL:

----
python rest_ssl_target.py
----

