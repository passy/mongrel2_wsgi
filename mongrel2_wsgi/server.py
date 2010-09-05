#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys
import urllib
from uuid import uuid4

from mongrel2 import handler
import json

from wsgiref.handlers import SimpleHandler
try:
    import cStringIO as StringIO
except:
    import StringIO

DEBUG = False

# setup connection handler
# sender_id is automatically generated 
# so that each handler instance is uniquely identified
conn = handler.Connection(str(uuid4()), 
        "tcp://127.0.0.1:9997",
        "tcp://127.0.0.1:9996")

def wsgi_server(application):
    '''WSGI handler based on the Python wsgiref SimpleHandler.
    
    A WSGI application should return a iterable op StringTypes. 
    Any encoding must be handled by the WSGI application itself.
    '''
    
    # TODO - this wsgi handler executes the application and renders a page 
    # in memory completely before returning it as a response to the client. 
    # Thus, it does not "stream" the result back to the client. It should be 
    # possible though. The SimpleHandler accepts file-like stream objects. So, 
    # it should be just a matter of connecting 0MQ requests/response streams to 
    # the SimpleHandler requests and response streams. However, the Python API 
    # for Mongrel2 doesn't seem to support file-like stream objects for requests 
    # and responses. Unless I have missed something.
    
    while True:
        if DEBUG: print "WAITING FOR REQUEST"
        
        # receive a request
        req = conn.recv()
        if DEBUG: print "REQUEST BODY: %r\n" % req.body
        
        if req.is_disconnect():
            if DEBUG: print "DISCONNECT"
            continue #effectively ignore the disconnect from the client
        
        # Set a couple of environment attributes a.k.a. header attributes 
        # that are a must according to PEP 333
        req.headers = dict((key.encode('ascii'), value.encode('ascii')) for (key,value) in req.headers.items())
        environ = {}
        environ['SERVER_PROTOCOL'] = 'HTTP/1.1' # SimpleHandler expects a server_protocol, lets assume it is HTTP 1.1
        environ['REQUEST_METHOD'] = req.headers['METHOD']
        if ':' in req.headers['Host']:
            environ['SERVER_NAME'] = req.headers['Host'].split(':')[0]
            environ['SERVER_PORT'] = req.headers['Host'].split(':')[1]
        else:
            environ['SERVER_NAME'] = req.headers['Host']
            environ['SERVER_PORT'] = ''
        environ['SCRIPT_NAME'] = '' # empty for now
		# 26 aug 2010: Apparently Mongrel2 has started (around 1.0beta1) to quote urls and
		# apparently Django isn't expecting an already quoted string. So, I just
		# unquote the path_info here again so Django doesn't throw a "page not found" on 
		# urls with spaces and other characters in it.
        environ['PATH_INFO'] = urllib.unquote(req.headers['PATH'])
        if '?' in req.headers['URI']:
            environ['QUERY_STRING'] = req.headers['URI'].split('?')[1]
        else:
            environ['QUERY_STRING'] = ''
        if req.headers.has_key('Content-Length'):
            environ['CONTENT_LENGTH'] = req.headers['Content-Length'] # necessary for POST to work with Django
        environ['wsgi.input'] = req.body
        
        for k,v in req.headers.items():
            k=k.replace('-','_').upper(); v=v.strip()
            if k in environ:
                continue                    # skip content length, type,etc.
            http_k = 'HTTP_'+k
            if http_k in environ:
                environ[http_k] += ','+v     # comma-separate multiple headers
            else:
                environ[http_k] = v
        
        
        if DEBUG: print "ENVIRON: %r\n" % environ
        
        # SimpleHandler needs file-like stream objects for
        # requests, errors and reponses
        reqIO = StringIO.StringIO(req.body)
        errIO = StringIO.StringIO()
        respIO = StringIO.StringIO()
        
        # execute the application
        handler = SimpleHandler(reqIO, respIO, errIO, environ, multithread = False, multiprocess = False)
        handler.run(application)
        
        # Get the response and filter out the response (=data) itself,
        # the response headers, 
        # the response status code and the response status description
        response = respIO.getvalue()
        response = response.split("\r\n")
        data = response[-1]
        headers = dict([r.split(": ") for r in response[1:-2]])
        code = response[0][9:12]
        status = response[0][13:]
        
        # strip BOM's from response data
        # Especially the WSGI handler from Django seems to generate them (2 actually, huh?)
        # a BOM isn't really necessary and cause HTML parsing errors in Chrome and Safari
        # See also: http://www.xs4all.nl/~mechiel/projects/bomstrip/
        # Although I still find this a ugly hack, it does work.
        data = data.replace('\xef\xbb\xbf', '')
        
        # Get the generated errors
        errors = errIO.getvalue()
        
        # return the response
        if DEBUG: print "RESPONSE: %r\n" % response
        if errors:
            if DEBUG: print "ERRORS: %r" % errors
            data = "%s\r\n\r\n%s" % (data, errors)            
        conn.reply_http(req, data, code = code, status = status, headers = headers)
