#!/usr/bin/python3

import pyromat as pm
import numpy as np
from flask import __version__ as flaskv
from flask import Flask,request
import os,sys

__version__ = '0.0'


###
# Custom request processing classes
#   These are designed to construct a JSON dictionary that will be used
#   by the HTML/JS on the client side to construct tables and plots.
#   
# Still to do... extend the arguments/return values to tolerate arrays
###

class PMGIRequest:
    args = {}
    out = {}
    s = None
    
    def __init__(self):
        self.args = {}
        self.s = None
        self.out['error'] = False
        self.out['message'] = ''
    
    def getid(self, idstr):
        """GETID - Retrieve a PYroMat object and fail gracefully
    getid(idstr)
    
Stores a PYroMat substance instance in the "s" member if successful.  If
unsuccessful, error is set to True, and an appropriate message is 
appended.

Returns False on success and True on failure.
"""
        self.s = pm.dat.data.get(idstr)
        if self.s is None:
            self.out['error'] = True
            self.out['message'] += f'Failed to find substance id {idstr}<br>\n'
            return True
        return False
        
    def require(self, types, mandatory):
        """REQUIRE - enforce rules about the request arguments
    require(types, mandatory)
    
TYPES       A dictionary of arguments and their types
MANDATORY   A list, set, or tuple of required argument names

Each keyword in TYPES corresponds to an argument that is allowed.  The
corresponding value in the dictionary must be a class or callable that
will be used to condition the argument's value.  For example, specifying
    types = {'teamname': str, 'players': int, 'color': str}
defines three optional arguments and their types.  More complicated 
requirements or conditioning can be applied in the appropriate __init__
definition.

Once defined in TYPES, an argument can be made mandatory by including 
its name in the MANDATORY list.

Returns True if an error occurs and False otherwise.
"""
        mandatory = set(mandatory)
        # Loop through the items
        for name,value in self.args.items():
            # Is this a recognized argument?
            if name not in types:
                self.out['error'] = True
                self.out['message'] += f'Unrecognized argument: {name}<br>\n'
                return True
            # If the argument is known
            try:
                self.args[name] = types[name](value)
            except:
                self.out['error'] = True
                self.out['message'] += f'Invalid argument: {name}={value}<br>\n'
                return True
            # If the argument is mandatory, check it off the list
            if name in mandatory:
                mandatory.remove(name)
        # Are there missing arguments?
        if mandatory:
            self.out['error'] = True
            self.out['message'] += f'Missing mandatory arguments:'
            prefix = ' '
            for name in mandatory:
                self.out['message'] += prefix + name
                prefix = ', '
            return True
        return False
    
    
class PropertyRequest(PMGIRequest):
    def __init__(self, args):
        # Clean initialization
        PMGIRequest.__init__(self)
        
        # Read in the arguments from raw
        self.args = dict(args)
        # Process the arguments
        if self.require(
                types = {'T':float, 'p':float, 'd':float, 'x':float, 'id':str},
                mandatory = ['id']):
            return
            
        # Retrieve the PM entry
        if self.getid(self.args['id']):
            return
        
            
    def process(self):
        # If there was an error, abort the processing
        if self.out['error']:
            return
        
        args = self.args.copy()            
        self.out['id'] = args.pop('id')

        try:
            self.out['T'] = float(self.s.T(**args))
            self.out['p'] = float(self.s.p(**args))
            self.out['d'] = float(self.s.d(**args))
            self.out['h'] = float(self.s.h(**args))
            self.out['s'] = float(self.s.s(**args))
        except:
            self.out['error'] = True
            self.out['message'] += 'Failed while evaluating properties<br>\n'
            self.out['message'] += str(sys.exc_info()[1]) + '<br>\n'


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
        
    pr = PropertyRequest(args)
    pr.process()
    return pr.out
        
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
    return {}

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
