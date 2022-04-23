#!/usr/bin/python3
import flask
import pyromat as pm
import numpy as np
from flask import __version__ as flaskv
from flask import Flask,request
import os,sys

__version__ = '0.0'


#### Helper functions
def toarray(a):
    try:
        return np.asarray(a, dtype=float)
    except ValueError:
        return np.asarray(a.split(','), dtype=float)


def json_friendly(dictdata):
    """
    Clean up a dictionary for output as JSON.
    """
    for name, value in dictdata.items():
        if isinstance(value, dict):
            json_friendly(value)
        elif isinstance(value, np.ndarray):
            if value.size == 1:
                dictdata[name] = np.asscalar(value)
            else:
                dictdata[name] = value.tolist()


###
# Custom request processing classes
#   These are designed to construct a JSON dictionary that will be used
#   by the HTML/JS on the client side to construct tables and plots.
###



class PMGIRequest:
    
    def __init__(self):
        self.args = {}
        self.substance = None
        self.out = {'error':False, 'message':''}

    def init_subst(self, idstr):
        """INIT_SUBST - Retrieve a PYroMat object and fail gracefully
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
        for name, value in self.args.items():
            # Is this a recognized argument?
            if name not in types:
                self.error(f'Unrecognized argument: {name}')
                return True
            # If the argument is known
            try:
                self.args[name] = types[name](value)  # Cast to type
            except:
                self.error(f'Invalid argument: {name}={value}')
                return True
            # If the argument is mandatory, check it off the list
            if name in mandatory:
                mandatory.remove(name)
        # Are there missing arguments?
        if mandatory:
            self.error(f'Missing mandatory arguments:')
            prefix = ' '
            for name in mandatory:
                self.warn(prefix + name, append_newline=False)
                prefix = ', '
            self.warn('')
            return True
        return False

    def error(self, message, append_newline=True):
        """
        Set flag for error and append an error message.
        """
        self.out['error'] = True
        self.out['message'] += message
        if append_newline:
            self.out['message'] += "\n"

    def warn(self, message, append_newline=True):
        """
        Append warning messages.
        """
        self.out['message'] += message
        if append_newline:
            self.out['message'] += "\n"


class PropertyRequest(PMGIRequest):
    def __init__(self, args, units=None):
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
                    'e': toarray,
                    'T': toarray,
                    'p': toarray,
                    'd': toarray,
                    'v': toarray,
                    'x': toarray,
                    'id': str
                },
                mandatory=['id']):
            return

        # Config the units
        if units is not None:
            try:
                InfoHandler.set_units(units)
            except pm.utility.PMParamError as e:
                self.error(e.args[0])

        # Retrieve the PM entry
        if self.init_subst(self.args['id']):
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
            self.error('Substance data seems to be corrupt!  Halting.')
            return

        #
        # Case out whether to use ideal gas or multi-phase processing
        #
        if self.substance.data['id'].startswith('ig'):
            self._ig_process()
        elif self.substance.data['id'].startswith('mp'):
            self._mp_process()
        else:
            self.error(f'Could not determine the collection for substance: {self.substance.data["id"]}')
            return

        # Finally, clean up the return parameters
        json_friendly(self.out)

    def _ig_process(self):
        self.error('THE IG PROCESS IS NOT WRITTEN YET!\nSorry for shouting')

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
        except (pm.utility.PMParamError, pm.utility.PMAnalysisError) as e:
            # Add in the error response from pyromat
            self.error(e.args[0])
            self.error('Args found:', append_newline=False)
            prefix = '  '
            for name in args:
                self.warn(prefix + name, append_newline=False)
                prefix = ', '
            self.warn('')
            return


class InfoHandler:
    _valid_unit_strs = ['energy', 'force', 'length', 'mass', 'molar', 'pressure', 'temperature', 'time', 'volume']

    @staticmethod
    def list_valid_substances(search_str=None):
        proplist = ['T', 'p', 'd', 'v', 'cp', 'cv', 'gam', 'e', 'h', 's', 'x', 'X', 'Y']
        out = {}
        dat = pm.search(search_str)
        for subst in dat:
            key = subst.data['id']
            out[key] = {}
            out[key]['prefix'] = subst.data['id'].split('.')[0]
            out[key]['id'] = subst.data['id']
            out[key]['class'] = subst.data['class']
            if 'names' in subst.data:
                out[key]['names'] = subst.data['names']
            else:
                out[key]['names'] = []
            out[key]['props'] = []
            for prop in proplist:
                if hasattr(subst, prop):
                    out[key]['props'].append(prop)

        return out

    @staticmethod
    def set_units(units):
        units = dict(units)

        for name, value in units.items():
            if name in InfoHandler._valid_unit_strs and \
                    value in InfoHandler.list_valid_units(name):
                pm.config['unit_'+name] = value
            else:
                raise pm.utility.PMParamError("Invalid unit specification:"
                                              f"{name}={value}")


    @staticmethod
    def get_units():
        out = {}
        cfg = pm.config
        for key in cfg.entries:
            if key.startswith('unit') and \
                    key.split('_')[1] in InfoHandler._valid_unit_strs:
                        out[key.split('_')[1]] = cfg[key]
        return out

    @staticmethod
    def list_valid_units(units=None):
        out = {}

        if units is None:
            units = InfoHandler._valid_unit_strs

        if type(units) is str:
            unitfun = getattr(pm.units, units)
            out = list(unitfun.get())
        else:
            for unit in units:
                unitfun = getattr(pm.units, unit)
                out[unit] = list(unitfun.get())
        return out


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
    # Read in the request data to an args dict
    if request.method == 'POST':
        jsondat = dict(request.json)
        args = jsondat['state_input']
        units = None
        if 'units' in jsondat:
            units = (jsondat['units'])
        pr = PropertyRequest(args, units)
    elif request.method == 'GET':
        args = dict(request.args)
        pr = PropertyRequest(args)

    pr.process()

    # Check for error and return code
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
    return {
        'substances': InfoHandler.list_valid_substances(),
        'units': InfoHandler.get_units(),
        'valid_units': InfoHandler.list_valid_units()
    }

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


# ##### DELETE ME FOR DEPLOY - ROUTE FOR SERVING STATIC HTML DURING DEV:
# ##### USE CASE - navigate to http://127.0.0.1:5000/index to browse page at:
# ##### /static/index.html
@app.route('/<string:page_name>/')
def render_static(page_name):
    if not app.debug:
        flask.abort(404)
    return app.send_static_file('%s.html' % page_name)


if __name__ == '__main__':
    app.run()
