#!/usr/bin/env python

'''
Peach CI Cloud Generic Integration Runner
Copyright (c) 2016 Peach Fuzzer, LLC

This script is used when the build/test environment only
has outbound network access to Peach API Security.  This
script will create a network tunnel using SSH to allow
communication two and from the proxy.

This script provides generic integration with CI systems by
running a command that returns non-zero when testing did not pass.
The vast majority of CI systems support this method of integration.

If a specific integration is offered for your CI system that is
preferred over this generic integration.
'''

from __future__ import print_function
import logging, os, sys, re

## Configuration

# JUnit
try:
    junit = os.environ["PEACH_JUNIT"]
except:
    junit = None

# Exit code when testing passed
try:
    exit_code_ok = int(os.environ["PEACH_EXIT_CODE_OK"])
except:
    exit_code_ok = 0

# Exit code when testing failed
try:
    exit_code_failure = int(os.environ["PEACH_EXIT_CODE_FAILURE"])
except:
    exit_code_failure = 1

# Exit code when error occurred during testing
try:
    exit_code_error = int(os.environ["PEACH_EXIT_CODE_ERROR"])
except:
    exit_code_error = 100

# SSH Identify file path
try:
    peach_ssh_user = os.environ["PEACH_SSH_USER"]
except:
    print("Error, missing PEACH_SSH_USER environment variable.")
    sys.exit(exit_code_error)

# SSH Identify file path
try:
    peach_ssh_id = os.environ["PEACH_SSH_ID"]
except:
    print("Error, missing PEACH_SSH_ID environment variable.")
    sys.exit(exit_code_error)

# SSH Host
try:
    peach_ssh_host = os.environ["PEACH_SSH_HOST"]
except:
    print("Error, missing PEACH_SSH_HOST environment variable.")
    sys.exit(exit_code_error)

# SSH Port
try:
    peach_ssh_port = int(os.environ["PEACH_SSH_PORT"])
except:
    print("Error, missing PEACH_SSH_PORT environment variable.")
    sys.exit(exit_code_error)

# Test automation launch script
# Command line or None to disable
try:
    automation_cmd = os.environ["PEACH_AUTOMATION_CMD"]
except:
    print("Error, missing PEACH_AUTOMATION_CMD environment variable.")
    sys.exit(exit_code_error)

# Configuration to start
project_config = None

try:
    project_config_file = os.environ["PEACH_CONFIG"]
except:
    print("Error, missing PEACH_CONFIG environment variable.")
    sys.exit(exit_code_error)

try:
    profile = os.environ["PEACH_PROFILE"]
except:
    print("Error, missing PEACH_PROFILE environment variable.")
    sys.exit(exit_code_error)

# Peach API url
peach_api = "http://127.0.0.1:5000"

# Peach UI URL
try:
    peach_ui = os.environ["PEACH_UI"]
except:
    peach_ui = peach_api

# Verbose output
try:
    verbose = bool(os.environ["PEACH_VERBOSE"])
except:
    verbose = False

# Enable logging to syslog
try:
    syslog_host = os.environ["PEACH_SYSLOG_HOST"]
    
    try:
        syslog_port = int(os.environ["PEACH_SYSLOG_PORT"])
    except:
        syslog_port = 514
    
    syslog_enabled = True
    syslog_level = logging.ERROR
    syslog_level = logging.INFO
    
except:
    syslog_enabled = False
    syslog_host = 'logserver.foobar.com'
    syslog_port = 514
    syslog_level = logging.ERROR
    syslog_level = logging.INFO

###############################################################
## DO NOT EDIT BELOW THIS LINE
###############################################################

import os

try:
    import peachproxy
except:
    print("Detected missing dependency 'peachproxy' python module.")
    print("Install: pip install peachproxy")
    exit(exit_code_error)

try:
    from requests import get, post, delete
except:
    print("Detected missing dependency 'requests' python module.")
    print("Install: pip install requests")
    exit(exit_code_error)

try:
    import psutil
except:
    print("Detected missing dependency 'psutil' python module.")
    print("Install: pip install psutil")
    exit(exit_code_error)

import requests, json, sys
import subprocess, signal
import logging, logging.handlers
from time import sleep
import sys
reload(sys)
sys.setdefaultencoding("utf-8")

logger = logging.getLogger(__name__)

logger.setLevel(syslog_level)
logFormatter = logging.Formatter("%(asctime)s [%(levelname)-5.5s] Peach Web CI: %(message)s")

if syslog_enabled:
    syslogHandler = logging.handlers.SysLogHandler(address=(syslog_host, syslog_port))
    syslogHandler.setFormatter(logFormatter)
    logger.addHandler(syslogHandler)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)

logger.info("Peach Web CI Cloud Generic Starting")

logger.info(" ")
logger.info("  Peach API Security UI: %s", peach_ui)
logger.info(" ")

logger.info("  automation_cmd: %s", automation_cmd)
logger.info("  exit_code_ok: %d", exit_code_ok)
logger.info("  exit_code_failure: %d", exit_code_failure)
logger.info("  exit_code_error: %d", exit_code_error)
logger.info("  peach_api: %s", peach_api)
logger.info("  project_config: %s", project_config)
logger.info("  project_config_file: %s", project_config_file)
logger.info("  junit: %s", junit)
logger.info("  syslog_enabled: %s", syslog_enabled )
if syslog_enabled:
    logger.info("  syslog_host: %s", syslog_host)
    logger.info("  syslog_port: %d", syslog_port)

test_process = None
peach_jobid = None

ssh_ctl_api = "peach-api.ssh.ctl"
ssh_ctl_proxy = "peach-proxy.ssh.ctl"
ssh_ctl_target = "peach-target.ssh.ctl"


# Load configuration file if provided
if not project_config and project_config_file:
    with open(project_config_file) as fd:
        project_config = fd.read()

try:
    from subprocess import DEVNULL
except ImportError:
    import os
    DEVNULL = open(os.devnull, 'wb')

def kill_proc_tree(pid, including_parent=True):
    '''Try and kill the pid's process tree
    '''
    
    parent = psutil.Process(pid)
    children = parent.children(recursive=True)
    for child in children:
        child.kill()
    psutil.wait_procs(children, timeout=5)
    if including_parent:
        parent.kill()
        parent.wait(5)

def shutdown():
    '''Perform clean shutdown of CI script
    '''
    
    if test_process:
        try:
            kill_proc_tree(test_process.pid)
            kill_proc_tree(test_process.pid)
            while not test_process.poll():
                os.killpg(os.getpgid(test_process.pid), signal.SIGTERM)
                test_process.terminate()
                test_process.kill()
                test_process.wait()
        except:
            pass

    if peach_jobid:
        peachproxy.session_teardown()
    
    # Close down any SSH tunnels
    os.system("ssh -T -O \"exit\" -S %s %s:%d" % (ssh_ctl_api, peach_ssh_host, peach_ssh_port))
    os.system("ssh -T -O \"exit\" -S %s %s:%d" % (ssh_ctl_proxy, peach_ssh_host, peach_ssh_port))
    os.system("ssh -T -O \"exit\" -S %s %s:%d" % (ssh_ctl_target, peach_ssh_host, peach_ssh_port))
    
def eexit(code):
    '''Close all processes and exit with 'code'
    '''
    
    logger.info("eexit(%d)", code)

    shutdown()
    
    exit(code)

import atexit
@atexit.register
def goodbye():
    '''Make sure we close out cleanly
    '''
    
    shutdown()

# Start SSH to Peach API

# -f  Requests ssh to go to background just before command execution
# -N  Do not execute a remote command.
# -T  Disable pseudo-terminal allocation
# -M  Places the ssh client into master mode for connection sharing
# -S  Specifies the location of a control socket for connection sharing
# -i  Selects a file from which the identity (private key) for public key authentication is read

logger.info("Port 5001")
os.system("ssh -f -i %s -p %d -N -T -M -L 127.0.0.1:5000:127.0.0.1:5000 -S %s %s@%s" % (peach_ssh_id, peach_ssh_port, ssh_ctl_api, peach_ssh_user, peach_ssh_host))
logger.info("Port 7777/8888")
os.system("ssh -f -i %s -p %d -N -T -M -R 8888:127.0.0.1:7777 -S %s %s@%s" % (peach_ssh_id, peach_ssh_port, ssh_ctl_target, peach_ssh_user, peach_ssh_host))

# Start job
try:
    logger.info("Starting session")
    peach_jobid = None
    
    peachproxy.session_setup(project_config, profile, peach_api)
    peach_jobid = str(peachproxy.session_id())
    peach_proxy = str(peachproxy.proxy_url())
    
    proxy_port = int(re.search(":(\d+)", peach_proxy).group(1))
    peach_proxy = "http://127.0.0.1:%d" % proxy_port

except Exception as ex:
    logger.critical("Error starting session: %s", ex)
    eexit(exit_code_failure)

# Start SSH to Peach Proxy

logger.info("Poroxy port")
os.system("ssh -f -i %s -p %d -N -T -M -L %d:127.0.0.1:%d -S %s %s@%s" % (peach_ssh_id, peach_ssh_port, proxy_port, proxy_port, ssh_ctl_proxy, peach_ssh_user, peach_ssh_host))

try:
    
    # Launch test automation
    
    if automation_cmd:
        
        logger.info("Launching test automation")
        logger.info("  PEACH_SESSIONID: %s", peach_jobid)
        logger.info("  PEACH_API: %s", peach_api)
        logger.info("  PEACH_PROXY: %s", peach_proxy)
        
        try:
            
            test_env = os.environ.copy()
            test_env["PEACH_SESSIONID"] = peach_jobid
            test_env["PEACH_API"] = peach_api
            test_env["PEACH_PROXY"] = peach_proxy
            
            if verbose:
                test_process = subprocess.Popen(
                    automation_cmd.split(),
                    env = test_env,
                )
            else:
                test_process = subprocess.Popen(
                    automation_cmd.split(),
                    env = test_env,
                    stdin=subprocess.PIPE, stdout=DEVNULL, stderr=subprocess.STDOUT
                )
            
            if not test_process:
                logger.critical("Unable to start test automation")
                eexit(exit_code_error)
            
            sleep(1)
            if test_process.poll():
                logger.critical("Unable to start test automation")
                eexit(exit_code_error)
            
        except Exception as ex:
            logger.critical("Error starting test automation: %s", ex)
            eexit(exit_code_error)
    
    else:
        logger.critical("No automated configured.  Currently required.")
        eexit(exit_code_error)
    
    # Wait for fuzzing to end
    
    logger.info("Waiting for job to complete")
    
    test_process.wait()

finally:
    logger.info("Ending session")
    
    ret = peachproxy.session_teardown()
    
    if junit:
        with open(junit, "wb+") as fd:
            fd.write(peachproxy.junit_xml())
    
    if ret:
        peach_jobid = None
        logger.info("Session Teardown indicated failures during testing.")
        eexit(exit_code_failure)
    
    eexit(exit_code_ok)    

# end
