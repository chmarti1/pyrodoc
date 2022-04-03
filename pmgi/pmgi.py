#!/usr/bin/python3

import pyromat as pm
import numpy as np
from flask import __version__ as flaskv
from flask import Flask,request
import os,sys

__version__ = '0.0'


####################
# Helper functions #
####################

# NOTE: I wrote this quickly to get something working.
# I actually think the right solution is to write a class that handles
# each type of request gracefully.  It should be initialized with the 
# POST/GET argument dictionary, and it should construct its own return
# message, error status, and it should carefully build the property 
# lookup arguments.
#
# This approach will be much more readable than what I ended up here.
# I immediately see irritation and pain trying to extend this to more 
# sophisticated interfaces.

def require(args, types={}, mandatory=[]):
    """REQUIRE - enforce argument requirements
    err,message = require(args, mandatory, optional)
    
ARGS        The dictionary of arguments and their values
TYPES       A dictionary of all recognized arguments and their types
MANDATORY   A list, set, or tuple of mandatory arguments

The values in the dictionaries are treated as the type/class specifiers
that will be used to convert/test the arguments.  Data conversion is 
done in-place on the args dictionary.

ERR         False unless an error occurs.
MESSAGE     A string error message
"""
    err = False
    message = ''
    mandatory = set(mandatory)
    
    for name,value in args.items():
        proto = types.get(name)
        # Is this argument recognized?
        if proto is None:
            err = True
            message = f'Unrecognized argument: {name}'
            return err,message
        # Attempt to convert it to the correct value
        try:
            value = proto(value)
        except:
            err = True
            message = f'Could not represent argument {name}={repr(value)} as type {repr(proto)}.'
        # It looks like everything is in order.
        # Time to overwrite the original value
        args[name] = value
        # If this is a mandatory argument, check it off the list
        if name in mandatory:
            mandatory.remove(name)
            
    # If there are any mandatory arguments that were not discovered
    if mandatory:
        err = True
        message = 'Missing mandatory arguments:'
        for name in mandatory:
            message += f' {name}'
    return err,message


def getid(idstr):
    """GET - wrapper for pm.get with graceful error handling
    
    s,message = get(idstr)
    
S           PYroMat substance object instance - None if error
MESSAGE     An error message string to pass to the application
"""
    try:
        s = pm.get(idstr)
        message = ''
    except:
        s = None
        message = f'Failed while looking for substance ID: {idstr}\n'
        message += str(sys.exc_info()[1])
    
    return s,message

############################
# Define the URL interface #
############################
app = Flask(__name__)
# Flask will see the route as relative to the apache WSGI alias
# The intent is that the WSGI root be set to pyromat.org/pmgi, so that
# will redirect here - to root.
#
# The root pmgi accepts property requests.
@app.route('/', methods=['POST', 'GET'])
def pmgi():
    out = {'message':''}
    args = {}
    # Read in the request data to an args dict
    if request.method == 'POST':
        args = dict(request.form)
    elif request.method == 'GET':
        args = dict(request.args)
        
    # parse arguments
    err,message = require(args,
        types={'id':str, 'call':str, 'T':float, 'p':float},
        mandatory=['id', 'call', 'T', 'p'])
    # Catch error
    if err:
        out['message'] = 'PMGI error: ' + message
        return out
        
    # Retrieve the substance
    s,message = getid(args['id'])
    if s is None:
        out['message'] = message
        return out
    
    # Retrieve the property method
    if not hasattr(s, args['call']):
        out['message'] = f'Substance {args["id"]} has no property {args["call"]}.'
        return out
        
    prop = getattr(s, args['call'])
    try:
        out[args['call']] = float(prop(T=args['T'], p=args['p']))
    except:
        out['message'] = f'Failed while calling property {args["id"]}.{args["call"]}'
    return out
    
# The get pmgi returns substance metadata
@app.route('/get', methods=['POST', 'GET'])
def get():
    out = {}
    if request.method == 'POST':
        pass
    elif request.method == 'GET':
        pass
    return out
        
# The info pmgi will return the results of queries (e.g. substance search)
@app.route('/info', methods=['POST', 'GET'])
def info():
    pass

# Version is responsible for returning basic system information 
# This will be important if users want to diagnose differences between
# local pyromat behaviors and webserver responses.
@app.route('/version')
def meta():
    out = {
        'python': sys.version.split()[0],
        'flask':flaskv, 
        'pyromat':pm.config['version'], 
        'pmgi':__version__,
        'numpy':np.version.full_version,
    }
    return out

if __name__ == '__main__':
    app.run()
