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

def clean(a):
    for name, value in a.items():
        if isinstance(value, dict):
            clean(value)
        elif isinstance(value, np.ndarray):
            if value.size == 1:
                a[name] = np.asscalar(value)
            else:
                a[name] = value.tolist()
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

        Stores a PYroMat substance instance in the "s" member if successful.
        If unsuccessful, error is set to True, and an appropriate message is
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
        will be used to condition the argument's value.  For example,
        specifying:
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
        if self.require(
                types=
                {
                    's': toarray,
                    'h': toarray,
                    'T': toarray,
                    'p': toarray,
                    'd': toarray,
                    'x': toarray,
                    'id': str
                },
                mandatory=['id']):
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
        clean(self.out)


    def _ig_process(self):
        self.error('THE IG PROCESS IS NOT WRITTEN YET!\nSorry for shouting\n')


    def _mp_process(self):
        """_mp_process

        The _mp_process and _ig_process methods are responsible for casing out
        the different valid property combinations to calculate all the rest.
        """
        args = self.args.copy()
        self.out['inputs'] = self.args
        # Leave only the property arguments
        args.pop('id')

        try:
            self.out['data'] = self.substance.state(**args)
        except pm.utility.PMParamError as e:
            self.error(e.args[0])
            self.error(' Args found:')
            prefix = '  '
            for name in args:
                self.warn(prefix + name)
                prefix = ', '
            return




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
    if pr.out['error']:
        return pr.out, 500
    else:
        return pr.out, 200

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
