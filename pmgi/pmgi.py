#!/usr/bin/python3
import flask
import pyromat as pm
import numpy as np
from flask import __version__ as flaskv
from flask import Flask, request
import sys

__version__ = '0.0'


# ### Helper functions
def toarray(a):
    try:
        return np.asarray(a, dtype=float)
    except ValueError:
        return np.asarray(a.split(','), dtype=float)


def compute_sat_state(subst, **kwargs):
    """
    Compute a state given any set of state properties
    :param subst: A pyromat substance object
    :param kwargs: The thermodynamic property at which to compute the states
                        specified by name. e.g. compute_sat_state(water, T=300)
    :return: (satLiqProps, satVapProps) - A full description of the states
                including all valid properties.
                Valid properties are: p,T,v,d,e,h,s,x
    """

    if not hasattr(subst, 'ps'):
        raise pm.utility.PMParamError('Saturation states not available for '
                                      f'{subst}.')

    kwargs = {k.lower(): v for k, v in kwargs.items()}
    if 'p' in kwargs:
        ps = np.array(kwargs['p']).flatten()
        Ts = subst.Ts(p=ps)
    elif 't' in kwargs:
        Ts = np.array(kwargs['t']).flatten()
        ps = subst.ps(T=Ts)
    else:
        raise pm.utility.PMParamError('Saturation state computation not '
                                      'supported for {}.'.format(kwargs.keys))

    sf, sg = subst.ss(T=Ts)
    hf, hg = subst.hs(T=Ts)
    df, dg = subst.ds(T=Ts)
    vf = 1/df
    vg = 1/dg
    ef, eg = subst.es(T=Ts)
    xf = np.zeros_like(sf)
    xg = np.ones_like(sg)
    liq_state = {
            'T': Ts,
            'p': ps,
            'd': df,
            'v': vf,
            'e': ef,
            's': sf,
            'h': hf,
            'x': xf
        }
    vap_state = {
            'T': Ts,
            'p': ps,
            'd': dg,
            'v': vg,
            'e': eg,
            's': sg,
            'h': hg,
            'x': xg
        }
    return liq_state, vap_state


def get_default_lines(subst, prop):
    """
    Get a default set of isolines for a given property.
    :param subst: A pyromat substance object
    :param prop: A string representing the requested property
    :return: vals - a np array of suitable default values.
    """
    if not hasattr(subst, prop):
        raise pm.utility.PMParamError(f"{subst} has no such property: {prop}")

    vals = None

    multiphase = hasattr(subst, 'ps')
    if multiphase:
        pmin, pmax = subst.plim()
        Tmin, Tmax = subst.Tlim()
    else:
        Tmin, Tmax = subst.Tlim()
        pmin, pmax = np.array([subst.p(T=Tmin, d=0.01), subst.p(T=Tmax, d=1000)]).flatten()

    if prop == 'p':
        peps = (pmax - pmin) / 1e6
        vals = np.logspace(np.log10(pmin + peps), np.log10(pmax - peps), 10)
    elif prop == 'T':
        Teps = (Tmax - Tmin) / 1000
        vals = np.linspace(Tmin + Teps, Tmax - Teps, 10)
    else:
        raise pm.utility.PMParamError(f'Default Lines Undefined for {prop}.')

    return vals


def compute_iso_line(subst, n=25, scaling='linear', **kwargs):
    """
    Compute a constant line for a given property at a given value
    :param subst: a pyromat substance object
    :param n: The number of points to compute to define the line
    :param scaling: Should point spacing be 'linear' or 'log'
    :param kwargs: A property specified by name. If 'default' is specified in
                    kwargs, the value of the prop will be ignored and a set
                    of default lines for that prop will be computed (see
                    get_default_lines()).
    :return: A dict containing arrays of properties. If 'default' flag is set
                the response will be an array of dicts representing all the
                individual lines.
    """

    # Perform a default computation
    if len(kwargs) != 1:
        if 'default' not in kwargs or len(kwargs) != 2:
            raise pm.utility.PMParamError("Specify exactly one property "
                                          "for an isoline")

    # Get an array of lines, ignore the value of prop.
    if 'default' in kwargs:
        kwargs.pop('default')
        prop = list(kwargs.keys())[0]  # only value left is prop
        lines = []
        # Recursively compute the single line
        for val in get_default_lines(subst, prop):
            arg = {prop: val}  # Build an argument
            lines.append(compute_iso_line(subst, n, scaling, **arg))
        return lines

    # We have a single property, so compute the line

    # Compute the limit pressures and temperatures
    multiphase = hasattr(subst, 'Ts')

    if multiphase:
        Tc, pc = subst.critical()
        # crit = subst.state(T=Tc, p=pc)
        pmin, pmax = subst.plim()
        Tmin, Tmax = subst.Tlim()
    else:
        Tc, pc = -999999, -999999
        Tmin, Tmax = subst.Tlim()
        pmin, pmax = np.array([subst.p(T=Tmin, d=0.01), subst.p(T=Tmax, d=1000)]).flatten()

    # The props for which we will plot against a T list
    if any(prop in kwargs for prop in ['p', 'd', 'v', 's', 'x']):

        # If quality, we stop at the crit pt
        if 'x' in kwargs:
            if multiphase:
                Tmax = Tc
            else:
                raise pm.utility.PMParamError('x cannot be computed for non-'
                                              'multiphase substances.')

        # An epsilon for the max/min
        Teps = (Tmax-Tmin)/1000

        line_T = np.linspace(Tmin + Teps, Tmax - Teps, n)

        # We can insert the phase change points
        if 'p' in kwargs and kwargs['p'] < pc:
            Tsat = subst.Ts(p=kwargs['p'])
            i_insert = np.argmax(line_T > Tsat)

            line_T = np.insert(line_T, i_insert, np.array([Tsat, Tsat]).flatten())
            x = -np.ones_like(line_T)
            x[line_T == Tsat] = np.array([0, 1])
            kwargs['x'] = x

        kwargs['T'] = line_T

    elif any(prop in kwargs for prop in ['T', 'h', 'e']):
        # ph & pe are going to be really slow, but what's better?
        peps = (pmax - pmin) / 1e6

        line_p = np.logspace(np.log10(pmin + peps), np.log10(pmax - peps), n)

        # We can insert the phase change points
        if 'T' in kwargs and kwargs['T'] < Tc:
            psat = subst.ps(T=kwargs['T'])
            i_insert = np.argmax(line_p > psat)

            line_p = np.insert(line_p, i_insert, np.array([psat, psat]).flatten())
            x = -np.ones_like(line_p)
            x[line_p == psat] = np.array([0, 1])
            kwargs['x'] = x

        kwargs['p'] = line_p

    else:  # Should never arrive here without error
        raise pm.utility.PMParamError('property invalid')

    states = subst.state(**kwargs)

    return states


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

    @staticmethod
    def json_friendly(somedict):
        """
        Clean up the out dictionary for output as JSON.
        """

        if isinstance(somedict, dict):
            for name, value in somedict.items():
                if isinstance(value, dict) or isinstance(value, list):
                    PMGIRequest.json_friendly(value)
                elif isinstance(value, np.ndarray):
                    if value.size == 1:
                        somedict[name] = np.asscalar(value)
                    else:
                        somedict[name] = value.tolist()
        elif isinstance(somedict, list):
            for item in somedict:
                PMGIRequest.json_friendly(item)

    @staticmethod
    def clean_nan(somedict):
        """
        Clean out nan values from a computed dict in place. Requires a dict of np arrays of equal length
        """

        if not hasattr(somedict, 'items') and isinstance(somedict, list):
            for item in somedict:
                PMGIRequest.clean_nan(item)
            return

        indices = np.array([], dtype=bool)
        for name, value in somedict.items():
            if isinstance(value, np.ndarray):
                if indices.size == 0:
                    indices = np.isnan(value)
                else:
                    indices = np.bitwise_or(indices, np.isnan(value))
            elif isinstance(value, dict):
                PMGIRequest.clean_nan(value)

        if indices.any():
            good = np.bitwise_not(indices)
            for name in somedict:
                somedict[name] = somedict[name][good]


class PropertyRequest(PMGIRequest):
    """
    This class will handle requests for properties at a fixed state or states.
    """
    def __init__(self, args, units=None):
        # Clean initialization
        PMGIRequest.__init__(self)

        # Read in the arguments from raw
        self.args = dict(args)
        # Process the arguments
        if self.require(
                types={
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
                InfoRequest.set_units(units)
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
            self.error(f'Could not determine the collection for substance: '
                       f'{self.substance.data["id"]}')
            return

        # Finally, clean up the return parameters
        PMGIRequest.clean_nan(self.out['data'])
        PMGIRequest.json_friendly(self.out)

    def _ig_process(self):
        return self._mp_process()  # works for now

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


class IsolineRequest(PMGIRequest):
    """
    This class will handle requests for an isoline
    """
    def __init__(self, args, units=None):
        # Clean initialization
        PMGIRequest.__init__(self)

        # Read in the arguments from raw
        self.args = dict(args)
        # Process the arguments
        if self.require(
                types={
                    's': toarray,
                    'h': toarray,
                    'e': toarray,
                    'T': toarray,
                    'p': toarray,
                    'd': toarray,
                    'v': toarray,
                    'x': toarray,
                    'default': str,
                    'id': str
                },
                mandatory=['id']):
            return

        # Config the units
        if units is not None:
            try:
                InfoRequest.set_units(units)
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

        args = self.args.copy()
        self.out['inputs'] = self.args
        # Leave only the property arguments
        args.pop('id')

        try:
            self.out['data'] = compute_iso_line(self.substance, **args)
            PMGIRequest.clean_nan(self.out['data'])
            PMGIRequest.json_friendly(self.out)
        except (pm.utility.PMParamError, pm.utility.PMAnalysisError) as e:
            self.error(e.args[0])
        # Finally, clean up the return parameters


class SaturationRequest(PMGIRequest):
    """
    This class will handle requests for saturation properties.
    """
    def __init__(self, args, units=None):
        # Clean initialization
        PMGIRequest.__init__(self)

        # Read in the arguments from raw
        self.args = dict(args)
        # Process the arguments
        if self.require(
                types={
                    'T': toarray,
                    'p': toarray,
                    'id': str
                },
                mandatory=['id']):
            return

        # Config the units
        if units is not None:
            try:
                InfoRequest.set_units(units)
            except pm.utility.PMParamError as e:
                self.error(e.args[0])

        # Retrieve the PM entry
        if self.init_subst(self.args['id']):
            return

    def process(self):
        """Process the request
        This method is responsible for populating the "out" member dict with
        correctly formatted data that can be returned as a JSON object.

        If no property is specified, the entire steam dome will be returned
        """
        # If there was an error, abort the processing
        if self.out['error']:
            return
        elif not isinstance(self.substance, pm.reg.__basedata__):
            self.error('Substance data seems to be corrupt!  Halting.')
            return

        if self.substance.data['id'].startswith('mp'):
            if not ('p' in self.args or 'T' in self.args):
                self._mp_steamdome_process()
            else:
                self._mp_process()
        else:
            self.error(f'Substance does not have saturation properties: '
                       f'{self.substance.data["id"]}')
            return

        # Finally, clean up the return parameters
        PMGIRequest.clean_nan(self.out['data']['liquid'])
        PMGIRequest.clean_nan(self.out['data']['vapor'])
        PMGIRequest.json_friendly(self.out)

    def _mp_process(self):
        """_mp_process

        computes a full state of saturation properties
        """
        args = self.args.copy()
        self.out['inputs'] = self.args
        # Leave only the property arguments
        args.pop('id')

        try:
            liq, vap = compute_sat_state(self.substance, **args)
            self.out['data'] = {}
            self.out['data']['liquid'] = liq
            self.out['data']['vapor'] = vap
        except (pm.utility.PMParamError, pm.utility.PMAnalysisError) as e:
            # Add in the error response from pyromat
            self.error(e.args[0])
            return

    def _mp_steamdome_process(self):
        """
        _mp_steamdome_process

        Compute the entire steam dome for the substance
        """
        n = 25
        scaling = 'linear'
        Tc, pc = self.substance.critical()
        critical = self.substance.state(T=Tc, p=pc)
        Tmin = self.substance.triple()[0]

        # Find valid limits
        Teps = (Tc - Tmin) / 1000

        line_T = np.linspace(Tmin, Tc-Teps, n).flatten()
        # line_T = np.logspace(np.log10(Tmin), np.log10(Tc-Teps), n).flatten()

        try:
            sll, svl = compute_sat_state(self.substance, T=line_T)

            # Append the critical point to the end of both lines
            satliq_states = {}
            satvap_states = {}
            for k in sll:
                satliq_states[k] = np.append(sll[k], critical[k])
                satvap_states[k] = np.append(svl[k], critical[k])

            self.out['data'] = {}
            self.out['data']['liquid'] = satliq_states
            self.out['data']['vapor'] = satvap_states

        except (pm.utility.PMParamError, pm.utility.PMAnalysisError) as e:
            # Add in the error response from pyromat
            self.error(e.args[0])
            return


class InfoRequest(PMGIRequest):
    """
    This class will handle generic info requests about pyromat data
    """
    _valid_unit_strs = ['energy', 'force', 'length', 'mass', 'molar',
                        'pressure', 'temperature', 'time', 'volume']

    def __init__(self):
        # Clean initialization
        PMGIRequest.__init__(self)

    def process(self):
        """Process the request
        This method is responsible for populating the "out" member dict with
        correctly formatted data that can be returned as a JSON object.
        """
        self.out['substances'] = InfoRequest.list_valid_substances()
        self.out['units'] = InfoRequest.get_units()
        self.out['valid_units'] = InfoRequest.list_valid_units()
        # If there was an error, abort the processing
        if self.out['error']:
            return

        # Finally, clean up the return parameters
        PMGIRequest.json_friendly(self.out)

    @staticmethod
    def set_units(units):
        units = dict(units)

        for name, value in units.items():
            if name in InfoRequest._valid_unit_strs and \
                    value in InfoRequest.list_valid_units(name):
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
                    key.split('_')[1] in InfoRequest._valid_unit_strs:
                out[key.split('_')[1]] = cfg[key]
        return out

    @staticmethod
    def list_valid_substances(search_str=None):
        proplist_out = ['T', 'p', 'd', 'v', 'e', 'h', 's', 'x',
                        'cp', 'cv', 'gam']
        proplist_in = ['T', 'p', 'd', 'v', 'e', 'h', 's', 'x']
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
            for prop in proplist_out:
                if hasattr(subst, prop):
                    out[key]['props'].append(prop)
            out[key]['inputs'] = []
            for prop in proplist_in:
                if hasattr(subst, prop):
                    out[key]['inputs'].append(prop)
        return out

    @staticmethod
    def list_valid_units(units=None):
        out = {}

        if units is None:
            units = InfoRequest._valid_unit_strs

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


# The saturation route computes saturation points or the steam dome
@app.route('/saturation', methods=['POST', 'GET'])
def sat():
    # Read in the request data to an args dict
    if request.method == 'POST':
        jsondat = dict(request.json)
        args = jsondat['state_input']
        units = None
        if 'units' in jsondat:
            units = (jsondat['units'])
        sr = SaturationRequest(args, units)
    elif request.method == 'GET':
        args = dict(request.args)
        sr = SaturationRequest(args)

    sr.process()

    # Check for error and return code
    if sr.out['error']:
        return sr.out, 500
    else:
        return sr.out, 200


# The isoline route computes isolines
@app.route('/isoline', methods=['POST', 'GET'])
def iso():
    # Read in the request data to an args dict
    if request.method == 'POST':
        jsondat = dict(request.json)
        args = jsondat['state_input']
        units = None
        if 'units' in jsondat:
            units = (jsondat['units'])
        isr = IsolineRequest(args, units)
    elif request.method == 'GET':
        args = dict(request.args)
        isr = IsolineRequest(args)

    isr.process()

    # Check for error and return code
    if isr.out['error']:
        return isr.out, 500
    else:
        return isr.out, 200


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
    ir = InfoRequest()
    ir.process()
    if ir.out['error']:
        return ir.out, 500
    else:
        return ir.out, 200


# Version is responsible for returning basic system information
# This will be important if users want to diagnose differences between
# local pyromat behaviors and webserver responses.
@app.route('/version')
def meta():
    out = {
        'python': sys.version.split()[0],
        'flask': flaskv,
        'pyromat': pm.config['version'],
        'pmgi': __version__,
        'numpy': np.version.full_version,
    }
    return out


# ##### DELETE ME FOR DEPLOY - ROUTE FOR SERVING STATIC HTML DURING DEV:
# ##### USE CASE - navigate to http://127.0.0.1:5000/index to browse page at:
# ##### /static/index.html
@app.route('/<string:page_name>/')
def render_static(page_name):
    # if not app.debug:
    #     flask.abort(404)
    return app.send_static_file('%s.html' % page_name)


if __name__ == '__main__':
    app.run()
