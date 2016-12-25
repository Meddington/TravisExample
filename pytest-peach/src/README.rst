pytest-peach
============

pytest-peach is a plugin for `py.test <http://pytest.org>`_ that integrates with
`Peach API Security <http://peachfuzzer.com>`.  Integration includes calling the
correct Peach Fuzzer APIs to report test names and not fuzzing setup and teardown requests.

== Requirements

You will need the following prerequisites in order to use pytest-peach:

- Python 2.6, 2.7, 3.2, 3.3, 3.4, 3.5 or PyPy
- py.test 2.8 or newer
- Requests v2.11 or newer

== Installation

To install pytest-peach:

----
$ pip install pytest-peach
----

*From Source*

----
$ python setup.py install
----

== Usage

The integration is intended to be run from CI integrations such as the
generic CI runner.
Several environmental variables are expected to have been set:

 - PEACH_API
 - PEACH_SESSIONID
 - PEACH_PROXY

----
pytest --peach test_target.py
----

=== Arguments

==== Required

--peach::
   This argument enables the pytest Peach API Security extention.

