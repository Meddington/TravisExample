
'''Peach Proxy Python Module
Copyright (c) 2016 Peach Fuzzer, LLC

This is a python module that provides method to call
the Peach Proxy Restful API.  This allows users
to integrate into unit-tests or custom traffic generators.
'''

from __future__ import print_function
import os, warnings, logging
import requests, json, sys
from requests import put, get, delete, post

logger = logging.getLogger(__name__)

logger.setLevel(logging.INFO)

logFormatter = logging.Formatter("%(asctime)s [%(levelname)-5.5s] %(message)s")
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)

#fileHandler = logging.FileHandler('peachproxy.log')
#fileHandler.setFormatter(logFormatter)
#logger.addHandler(fileHandler)

## This code will block the use of proxies.

session = requests.Session()
session.trust_env = False

## Peach Proxy API Helper Functions

__peach_session = None
__peach_api = None
__peach_state = "Continue"
__peach_proxy = None

## Setter/getter functions

def state():
    '''Current state of Peach Proxy
    '''
    global __peach_state
    return __peach_state

def session_id():
    '''Get the current sessions id
    '''
    global __peach_session
    return __peach_session['Id']

def set_session_id(session_id):
    '''Get the current sessions id
    '''
    global __peach_session
    if __peach_session == None:
        __peach_session = {}
        
    __peach_session['Id'] = session_id

def proxy_url():
    '''Get the current sessions proxy url
    '''
    global __peach_session
    return __peach_session['ProxyUrl']

def set_proxy_url(url):
    '''Get the current sessions proxy url
    '''
    global __peach_session
    if __peach_session == None:
        __peach_session = {}
        
    __peach_session['ProxyUrl'] = url

def set_peach_api(api):
    '''Get the current sessions proxy url
    '''
    global __peach_api
    __peach_api = api
    
## Attempt to load from environment

try:
    set_peach_api(os.environ["PEACH_API"])
    set_session_id(os.environ["PEACH_SESSIONID"])
    set_proxy_url(os.environ["PEACH_PROXY"])
except:
    pass

def session_setup(project, profile, api):
    '''Notify Peach Proxy that a test session is starting.
    Called ONCE at start of testing.

    Keyword arguments:
    project -- Configuration to launch
    profile -- Name of profile within project to launch
    api -- Peach API URL, example: http://127.0.0.1:5000
    '''

    logger.debug(">>session_setup")

    global __peach_session
    global __peach_api

    __peach_api = api

    try:
        url = "%s/api/sessions?profile=%s" % (api, profile)

        headers = {
            'Content-Type' : 'application/json',
        }
        
        if type(project) is str:
            data = project
        else:
            # sort_keys is *required* in order for the $type field to be first in any nested type.
            data = json.dumps(project, sort_keys=True)

        r = session.post(url, data=data, headers=headers)
        if r.status_code != 200:
            logger.error('Error calling /api/sessions: %s', r.status_code)
            sys.exit(-1)

        __peach_session = r.json()
        
        logger.info("Session ID: %s", session_id())
        logger.info("Proxy URL: %s", proxy_url())

    except requests.exceptions.RequestException as e:
        logger.error("Error communicating with Peach Fuzzer.")
        logger.error("vvvv ERROR vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv")
        logger.error(e)
        logger.error("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
        sys.exit(-1)

def session_teardown():
    '''Notify Peach Proxy that a test session is ending.

    Called ONCE at end of testing. This will cause Peach to stop.
    
    Returns:
        bool: True says failures found during testing
              False says testing completed without issue
    '''
    
    logger.debug(">>session_teardown")

    global __peach_session
    if not __peach_session:
        logger.error("Called session_teardown() w/o a session id")
        sys.exit(-1)

    global __peach_api
    if not __peach_api:
        logger.error("Called session_teardown() w/o a peach_api url")
        sys.exit(-1)

    try:
        r = session.delete("%s/api/sessions/%s" % (__peach_api, session_id()))
        if r.status_code != 200:
            logger.error('Error deleting session via /api/sessions/id: %s', r.status_code)
            sys.exit(-1)
        
        r = r.json()
        return r
    except requests.exceptions.RequestException as e:
        logger.error("Error communicating with Peach Fuzzer.")
        logger.error("vvvv ERROR vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv")
        logger.error(e)
        logger.error("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
        sys.exit(-1)

def setup():
    '''Notify Peach Proxy that setup tasks are about to run.

    This will disable fuzzing of messages so the setup tasks
    always work OK.
    '''
    
    logger.debug(">>setup()")

    global __peach_session
    if not __peach_session:
        logger.error("Called setup() w/o a session id")
        sys.exit(-1)

    global __peach_api
    if not __peach_api:
        logger.error("Called setup() w/o a peach_api url")
        sys.exit(-1)

    try:
        r = session.post("%s/api/sessions/%s/TestSetUp" % (__peach_api, session_id()))
        if r.status_code != 200:
            logger.error("Error sending TestSetUp for session '%s': %s %s",
                         session_id(), r.status_code, r.reason)
            sys.exit(-1)
    except requests.exceptions.RequestException as e:
        logger.error("Error communicating with Peach Fuzzer.")
        logger.error("vvvv ERROR vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv")
        logger.error(e)
        logger.error("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
        sys.exit(-1)

def teardown():
    '''Notify Peach Proxy that teardown tasks are about to run.

    This will disable fuzzing of messages so the teardown tasks
    always work OK.
    
    Returns:
        str: Returns a string indicating next action
             Continue - Produce another of the current test case,
             NextTest - Move to next test case if any
             Error - Non-recoverable error has occurred. Exit.
    '''
    
    logger.debug(">>teardown")

    global __peach_session
    if not __peach_session:
        logger.error("Called teardown() w/o a session id")
        sys.exit(-1)

    global __peach_api
    if not __peach_api:
        logger.error("Called teardown() w/o a peach_api url")
        sys.exit(-1)

    try:
        r = session.post("%s/api/sessions/%s/TestTearDown" % (__peach_api, session_id()))
        if r.status_code != 200:
            logger.error('Error sending TestTearDown: %s', r.status_code)
            sys.exit(-1)
        
        global __peach_state
        __peach_state = str(r.json())
        
        logger.debug("<<teardown: state: %s", __peach_state)
        
        return __peach_state
            
    except requests.exceptions.RequestException as e:
        logger.error("Error communicating with Peach Fuzzer.")
        logger.error("vvvv ERROR vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv")
        logger.error(e)
        logger.error("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
        sys.exit(-1)

def suite_teardown():
    '''Notify Peach that traffic generator has completed

    Normally this is called once the result of teardown() has indicate
    Peach has finished testing.  However, in the case that the
    traffic generator encounters a non-recoverable error,
    suite_teardown() will cause the Peach Job to error.
    '''
    
    logger.debug(">>suite_teardown")

    global __peach_session
    if not __peach_session:
        logger.error("Called suite_teardown() w/o a session id")
        sys.exit(-1)

    global __peach_api
    if not __peach_api:
        logger.error("Called suite_teardown() w/o a peach_api url")
        sys.exit(-1)

    try:
        r = session.post("%s/api/sessions/%s/TestSuiteTearDown" % (__peach_api, session_id()))
        if r.status_code != 200:
            logger.error('Error sending TestSuiteTearDown: %s', r.status_code)
            sys.exit(-1)
            
    except requests.exceptions.RequestException as e:
        logger.error("Error communicating with Peach Fuzzer.")
        logger.error("vvvv ERROR vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv")
        logger.error(e)
        logger.error("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
        sys.exit(-1)

def testcase(name):
    '''Notify Peach Proxy that a test case is starting.
    This will enable fuzzing and group all of the following
    requests into a group.

    Keyword arguments:
    name -- Name of unit test. Shows up in metrics.
    '''
    
        
    logger.debug(">>testcase(%s)", name)

    global __peach_session
    if not __peach_session:
        return

    global __peach_api
    if not __peach_api:
        return

    try:
        r = session.post("%s/api/sessions/%s/testRun?name=%s" % (__peach_api, session_id(), name))
        if r.status_code != 200:
            logger.error('Error sending testRun: %s', r.status_code)
            sys.exit(-1)
    except requests.exceptions.RequestException as e:
        logger.error("Error communicating with Peach Fuzzer.")
        logger.error("vvvv ERROR vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv")
        logger.error(e)
        logger.error("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
        sys.exit(-1)

def junit_xml():
    '''Generate JUnit style XML output for use with CI integration.
    '''
        
    logger.debug(">>junit_xml")

    global __peach_session
    if not __peach_session:
        return

    global __peach_api
    if not __peach_api:
        return
    
    try:
        r = session.get("%s/api/jobs/%s/junit" % (__peach_api, session_id()))
        if r.status_code != 200:
            logger.error('Error sending testRun: %s', r.status_code)
            sys.exit(-1)
        
        return r.text
        
    except requests.exceptions.RequestException as e:
        logger.error("Error communicating with Peach Fuzzer.")
        logger.error("vvvv ERROR vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv")
        logger.error(e)
        logger.error("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
        sys.exit(-1)
   

if __name__ == "__main__":

    print("This is a python module and should only be used by other")
    print("Python programs.  It was not intended to be run directly.")
    print("\n")
    print("For more information see the README")

# end
