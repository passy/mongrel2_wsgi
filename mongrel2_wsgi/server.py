#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys
import urllib
from uuid import uuid4

import json

from wsgiref.handlers import SimpleHandler
try:
    import cStringIO as StringIO
except:
    import StringIO

DEBUG = False

def random_uuid():
    return str(uuid4())

def wsgi_server(application, conn):
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
    
    # setup connection handler
    # sender_id is automatically generated 
    # so that each handler instance is uniquely identified

    while True:
        if DEBUG: print "WAITING FOR REQUEST"
        
        # receive a request
        req = conn.recv()
        if DEBUG: print "REQUEST BODY: %r\n" % req.body
        
        if req.is_disconnect():
            if DEBUG: print "DISCONNECT"
            continue #effectively ignore the disconnect from the client
        
        # Set a couple of envment attributes a.k.a. header attributes 
        # that are a must according to PEP 333
        req.headers = dict((key.encode('ascii'), value.encode('ascii')) for (key,value) in req.headers.items())
        env = {}
        env['SERVER_PROTOCOL'] = 'HTTP/1.1' # SimpleHandler expects a server_protocol, lets assume it is HTTP 1.1
        env['REQUEST_METHOD'] = req.headers['METHOD']
        if ':' in req.headers['Host']:
            env['SERVER_NAME'] = req.headers['Host'].split(':')[0]
            env['SERVER_PORT'] = req.headers['Host'].split(':')[1]
        else:
            env['SERVER_NAME'] = req.headers['Host']
            env['SERVER_PORT'] = ''
        env['SCRIPT_NAME'] = '' # empty for now
		# 26 aug 2010: Apparently Mongrel2 has started (around 1.0beta1) to quote urls and
		# apparently Django isn't expecting an already quoted string. So, I just
		# unquote the path_info here again so Django doesn't throw a "page not found" on 
		# urls with spaces and other characters in it.
        env['PATH_INFO'] = urllib.unquote(req.headers['PATH'])
        if '?' in req.headers['URI']:
            env['QUERY_STRING'] = req.headers['URI'].split('?')[1]
        else:
            env['QUERY_STRING'] = ''
        if req.headers.has_key('Content-Length'):
            env['CONTENT_LENGTH'] = req.headers['Content-Length'] # necessary for POST to work with Django
        env['wsgi.input'] = req.body
        
        for k,v in req.headers.items():
            k=k.replace('-','_').upper(); v=v.strip()
            if k in env:
                continue                    # skip content length, type,etc.
            http_k = 'HTTP_'+k
            if http_k in env:
                env[http_k] += ','+v     # comma-separate multiple headers
            else:
                env[http_k] = v
        
        
        if DEBUG: print "ENVIRON: %r\n" % env
        
        # SimpleHandler needs file-like stream objects for
        # requests, errors and reponses
        reqIO = StringIO.StringIO(req.body)
        errIO = StringIO.StringIO()
        respIO = StringIO.StringIO()
        
        # execute the application
        simple_handler = SimpleHandler(reqIO, respIO, errIO, env, multithread = False, multiprocess = False)
        simple_handler.run(application)
        
        class Response(object):
            def start_response(status, headers, exc_info=None):
                if exc_info is not None:
                    raise exc_info[0], exc_info[1], exc_info[2]
                captured[:] = [status, headers, exc_info]
                return output.append
                
        
        captured = []
        output = []

        app_iter = application(self.env, start_response)
        if output or not captured:
            try:
                output.extend(app_iter)
            finally:
                if hasattr(app_iter, 'close'):
                    app_iter.close()
            app_iter = output
        if catch_exc_info:
            return (captured[0], captured[1], app_iter, captured[2])
        else:
            return (captured[0], captured[1], app_iter)
        
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
