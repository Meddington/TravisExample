#!/usr/bin/env python

'''Example traffic generator in Python

Uses both the Peach Proxy API to notify when a test starts
and the python requests library to make HTTP calls.
'''

import os, json
from requests import put, get, delete, post
import requests, json, sys
import logging, logging.handlers
import requests
try:
	from requests.packages.urllib3.exceptions import InsecureRequestWarning
	requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
except ImportError:
	# looks like Debian/Ubuntu decided to 'unvendor' the urllib3 module
	pass

'''The peachproxy module provides helper methods for calling
the Peach Web Proxy APIs.  These api's are used to integrate
our traffic generator script with Peach.'''
import peachproxy

## Configuration options

cabundle = 'rootCA.pem'

enable_xml_target = False
if enable_xml_target:
	from simplexml import dumps, loads

# HTTP target
target = 'http://127.0.0.1:7777'
target_xml = 'http://127.0.0.1:6666'
req_args = {'headers': {"X-API-Key":"b5638ae7-6e77-4585-b035-7d9de2e3f6b3"}}
xml_req_args = {'headers':{"Accept":"application/xml","X-API-Key":"b5638ae7-6e77-4585-b035-7d9de2e3f6b3"}}

# HTTPS target
#target = 'https://127.0.0.1:7777'
#target_xml = 'https://127.0.0.1:6666'
#req_args = { 'verify' : False, 'headers':{"X-API-Key":"b5638ae7-6e77-4585-b035-7d9de2e3f6b3"} }
#xml_req_args = {'verify':False, 'headers':{"Accept":"application/xml","X-API-Key":"b5638ae7-6e77-4585-b035-7d9de2e3f6b3"}}

# HTTPS target with client cert
#target = 'https://127.0.0.1:7777'
#target_xml = 'https://127.0.0.1:6666'
#req_args = { 'cert' : ('clientcert.crt', 'clientcert.key'), 'verify' : False, 'headers':{"X-API-Key":"b5638ae7-6e77-4585-b035-7d9de2e3f6b3"} }
#xml_req_args = {'cert' : ('clientcert.crt', 'clientcert.key'), 'verify':False, 'headers':{"Accept":"application/xml","X-API-Key":"b5638ae7-6e77-4585-b035-7d9de2e3f6b3"}}

## Load values set by CI integration script

try:
	peach_sessionid = os.environ["PEACH_SESSIONID"]
	peach_api = os.environ["PEACH_API"]
	peach_proxy = os.environ["PEACH_PROXY"]

except:
	print ""
	print "Error, unable to locate one of the following environmental:"
	print "  PEACH_SESSIONID, PEACH_API, PEACH_PROXY"
	print ""
	print "Note: this script is intended to be launched by peach_ci_runner.py"
	print "      or another CI interface."
	
	sys.exit(0)

peachproxy.set_session_id(peach_sessionid)
peachproxy.set_proxy_url(peach_proxy)
peachproxy.set_peach_api(peach_api)

## Set proxy for requires library

'''Set proxy values for the HTTP library being used'''
os.environ["HTTP_PROXY"] = peachproxy.proxy_url()
os.environ["HTTPS_PROXY"] = peachproxy.proxy_url()
os.environ["REQUESTS_CA_BUNDLE"] = cabundle


## Test cases

def test_setup():
	'''
	Setup the test by clearing out created users.
	'''
	
	try:
		delete(target+'/api/users/2', **req_args)
		if enable_xml_target:
			delete(target_xml+'/api/users/2', **xml_req_args)
	except:
		pass
		
	try:
		delete(target+'/api/users?user=dd', **req_args)
		if enable_xml_target:
			delete(target_xml+'/api/users?user=dd', **xml_req_args)
	except:
		pass

def test_teardown():
	'''
	Teardown test by clearing out created users.
	'''
	
	try:
		delete(target+'/api/users/2', **req_args)
		if enable_xml_target:
			delete(target_xml+'/api/users/2', **xml_req_args)
	except:
		pass
		
	try:
		delete(target+'/api/users?user=dd', **req_args)
		if enable_xml_target:
			delete(target_xml+'/api/users?user=dd', **xml_req_args)
	except:
		pass

	pass

def test_user_create():
	
	r = post(target+'/api/users',
		 data=json.dumps({"user":"dd", "first":"mike", "last":"smith", "password":"hello"}),
		 **req_args)
	user = r.json()
	get(target+'/api/users', **req_args)
	get(target+'/api/users/%d' % user['user_id'], **req_args)
	delete(target+'/api/users/%d' % user['user_id'], **req_args)
	
	if enable_xml_target:
		r = post(target_xml+'/api/users',
			 data=dumps({'user':{"user":"dd", "first":"mike", "last":"smith", "password":"hello"}}),
			 **xml_req_args)
		
		if r.status_code != 200:
			raise Exception()
		
		user = loads(r.text)['response']
		get(target_xml+'/api/users', **xml_req_args)
		get(target_xml+'/api/users/%d' % int(user['user_id']), **xml_req_args)
		delete(target_xml+'/api/users/%d' % int(user['user_id']), **xml_req_args)

def test_user_update():
	
	r = post(target+'/api/users',
		data=json.dumps({"user":"dd", "first":"mike", "last":"smith", "password":"hello"}),
		**req_args)
	user = r.json()
	get(target+'/api/users/%d' % user['user_id'], **req_args)
	put(target+'/api/users/%d' % user['user_id'],
	    data=json.dumps({"user":"dd", "first":"mike", "last":"smith", "password":"hello"}),
	    **req_args)
	delete(target+'/api/users/%d' % user['user_id'], **req_args)
	get(target+'/api/users', **req_args)
	
	if enable_xml_target:
		r = post(target_xml+'/api/users',
			data=dumps({'user':{"user":"dd", "first":"mike", "last":"smith", "password":"hello"}}),
			**xml_req_args)
		
		if r.status_code != 200:
			raise Exception()
		
		user = loads(r.text)['response']
		get(target_xml+'/api/users/%d' % int(user['user_id']), **xml_req_args)
		put(target_xml+'/api/users/%d' % int(user['user_id']),
			data=dumps({"user":"dd", "first":"mike", "last":"smith", "password":"hello"}),
			**xml_req_args)
		delete(target_xml+'/api/users/%d' % int(user['user_id']), **xml_req_args)
		get(target_xml+'/api/users', **xml_req_args)

##############################
## Traffic Generation

try:
	
	print "\n\n----] test_user_create [----------------------------\n"
	
	# Generate traffic for this this test case until
	# Peach Web tells us to stop
	while True:
		print ".",
		
		'''Notify Peach we are doing test setup.  This will
		allow the traffic through with no modification (fuzzing off).'''
		peachproxy.setup()
		test_setup()
		
		'''Notify Peach we are performing a test.  This will enable
		fuzzing of the requests.  All requests will be considered
		part of this test case until another Peach Web Proxy API is
		called.'''
		peachproxy.testcase('test_user_create')
		
		try:
			test_user_create()
			print "P"
		#except Exception as ex:
		#	print ex
		except:
			print "E"
		
		'''Notify Peach our test case is complete and we are performing
		teardown/cleanup.  This will allow the traffic through with no
		modification (fuzzing off).
		
		Teardown will also return a bool indicating if we should
		continue to generate traffic for this test case.
		'''
		next_action = peachproxy.teardown()
		test_teardown()
		
		if next_action == 'Continue':
			continue
		elif next_action == 'NextTest':
			break
		elif next_action == 'Error':
			raise Exception()
	
	print "\n\n----] test_user_update [----------------------------\n"
	
	while True:
		print ".",
		peachproxy.setup()
		test_setup()
		
		peachproxy.testcase('test_user_update')
		
		try:
			test_user_update()
			print "P"
		except:
			print "E"
		
		next_action = peachproxy.teardown()
		test_teardown()
		
		if next_action == 'Continue':
			continue
		elif next_action == 'NextTest':
			break
		elif next_action == 'Error':
			raise Exception()

finally:
	peachproxy.suite_teardown()

# end
