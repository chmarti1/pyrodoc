#!/usr/bin/python3

import pyromat as pm
import numpy as np
from flask import __version__ as flaskv
from flask import Flask,request
import os,sys

__version__ = '0.0'


#### Helper functions
def toarray(a):
    return np.asarray(a.split(','), dtype=float)
    

###
# Custom request processing classes
#   These are designed to construct a JSON dictionary that will be used
#   by the HTML/JS on the client side to construct tables and plots.
#   
# Still to do... extend the arguments/return values to tolerate arrays
###



class PMGIRequest:
    
    def __init__(self):
        self.args = {}
        self.substance = None
        self.out = {'error':False, 'message':''}

    
    def getid(self, idstr):
        """GETID - Retrieve a PYroMat object and fail gracefully
    getid(idstr)
    
Stores a PYroMat substance instance in the "s" member if successful.  If
unsuccessful, error is set to True, and an appropriate message is 
appended.

Returns False on success and True on failure.
"""
        self.substance = pm.dat.data.get(idstr)
        if self.substance is None:
            self.out['error'] = True
            self.out['message'] += f'Failed to find substance id {idstr}\n'
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
                self.error(f'Unrecognized argument: {name}\n')
                return True
            # If the argument is known
            try:
                self.args[name] = types[name](value)
            except:
                self.error(f'Invalid argument: {name}={value}\n')
                return True
            # If the argument is mandatory, check it off the list
            if name in mandatory:
                mandatory.remove(name)
        # Are there missing arguments?
        if mandatory:
            self.error(f'Missing mandatory arguments:')
            prefix = ' '
            for name in mandatory:
                self.warn(prefix + name)
                prefix = ', '
            self.warn('\n')
            return True
        return False
    
    def error(self, message):
        self.out['error'] = True
        self.out['message'] += message
        
    def warn(self, message):
        self.out['message'] += message
    
class PropertyRequest(PMGIRequest):
    def __init__(self, args):
        # Clean initialization
        PMGIRequest.__init__(self)
        
        # Read in the arguments from raw
        self.args = dict(args)
        # Process the arguments
        if self.require( types = 
                {   's':toarray, 
                    'h':toarray, 
                    'T':toarray, 
                    'p':toarray, 
                    'd':toarray, 
                    'x':toarray, 
                    'id':str},
                mandatory = ['id']):
            return
            
        # Retrieve the PM entry
        if self.getid(self.args['id']):
            return
        
        
    def process(self):
        """Process the request
    This method is responsible for populating the "out" member dict with 
correctly formatted data that can be returned as a JSON object.  
"""
        # If there was an error, abort the processing
        if self.out['error']:
            return
        elif not isinstance(self.substance, pm.reg.__basedata__):
            self.error('Substance data seems to be corrupt!  Halting.\n')
            return
        
        #
        # Case out whether to use ideal gas or multi-phase processing
        #
        if self.substance.data['id'].startswith('ig'):
            self._ig_process()
        elif self.substance.data['id'].startswith('mp'):
            self._mp_process()
        else:
            self.error(f'Could not determine the collection for substance: {self.substance.data["id"]}\n')
            return
            
        # Finally, clean up the return parameters
        for name,value in self.out.items():
            if isinstance(value,np.ndarray):
                if value.size == 1:
                    self.out[name] = np.asscalar(value)
                else:
                    self.out[name] = value.tolist()
        
    def _ig_process(self):
        self.error('THE IG PROCESS IS NOT WRITTEN YET!\nSorry for shouting\n')
        
        
    def _mp_process(self):
        """_mp_process
        
The _mp_process and _ig_process methods are responsible for casing out
the different valid property combinations to calculate all the rest.
"""
        args = self.args.copy()
        self.out.update(args)
        # Leave only the property arguments
        args.pop('id')
        
        if len(args) != 2:
            self.error('Two properties are required.  Found:')
            prefix = '  '
            for name in args:
                self.warn(prefix + name)
                prefix = ', '
            return

        # We'll need to case out the inverse functions.  There are more
        # pythonic ways to do this using PYroMat's flexible interface, but
        # this way is more likely to fail gracefully or not at all.
        # 
        # In this first stage, we make sure we have Temperature and density
        # regardless of the other arguments.  Enthalpy and entropy are the
        # most nuanced, so we'll handle them first.
        T = None
        d = None
        if 'h' in args:
            if 'p' in args:
                try:
                    T,self.out['x'] = self.substance.T_h(args['h'], p=args['p'], quality=True)
                    self.out['T'] = T
                    self.out['d'] = d = self.substance.d(T=T,p=args['p'])
                except:
                    self.error('The state may not be valid. Returned with error:\n')
                    self.warn(str(sys.exc_info()[1]) + '\n')
                    return True
            elif 'd' in args:
                d = args['d']
                try:
                    T,self.out['x'] = self.substance.T_h(args['h'], d=args['d'], quality=True)
                    self.out['T'] = T
                except:
                    self.error('The state may not be valid. Returned with error:\n')
                    self.warn(str(sys.exc_info()[1]) + '\n')
                    return True
            else:
                self.error('Enthalpy (h) requires pressure (p) or density (d) to be specified.\nFound:')
                prefix = '  '
                for name in args:
                    self.warn(prefix + name)
                    prefix = ', '
                self.warn('\n')
                return True
            
        elif 's' in args:
            s = args['s']
            if 'T' in args:
                T = args['T']
                try:
                    d,self.out['x'] = self.substance.d_s(s=args['s'], T=T, quality=True)
                    self.out['d'] = d
                except:
                    self.error('The state may not be valid. Returned with error:\n')
                    self.warn(str(sys.exc_info()[1]) + '\n')
                    return True
            elif 'p' in args:
                try:
                    T,self.out['x'] = self.substance.T_s(s=args['s'], p=args['s'], quality=True)
                    self.out['T'] = T
                    self.out['d'] = d = self.substance.d(T=T, p=args['p'])
                except:
                    self.error('The state may not be valid. Returned with error:\n')
                    self.warn(str(sys.exc_info()[1]) + '\n')
                    return True
            elif 'd' in args:
                d = args['d']
                try:
                    T,self.out['x'] = self.substance.T_s(s=args['s'], d=args['d'], quality=True)
                    self.out['T'] = T
                except:
                    self.error('The state may not be valid. Returned with error:\n')
                    self.warn(str(sys.exc_info()[1]) + '\n')
                    return True
        # Now the simple cases - no inverse routines
        else:
            if 'T' in args:
                T = args['T']
            else:
                self.out['T'] = T = self.substance.T(**args)
            
            if 'd' in args:
                d = args['d']
            else:
                self.out['d'] = d = self.substance.d(**args)
        # Add in the missing properties
        try:
            if 'p' not in self.out:
                self.out['p'] = self.substance.p(T=T,d=d)
            if 'h' not in self.out:
                self.out['h'] = self.substance.h(T=T,d=d)
            if 's' not in self.out:
                self.out['s'] = self.substance.s(T=T,d=d)
            # add properties that are never accepted as arguments
            self.out['gam'] = self.substance.gam(T=T,d=d)
            self.out['cp'] = self.substance.cp(T=T,d=d)
            self.out['cv'] = self.substance.cv(T=T,d=d)
            
        except:
            self.error('Failed while evaluating properties\n')
            self.warn(str(sys.exc_info()[1]) + '\n')
            return True
            


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
