#!/usr/bin/python3
"""PYroMat Gateway Interface module

The PMGIRequest class is the parent of a number of child HTTP request
handling classes.  The classes are initialized with a request object
provided by the Flask package.  Request handling by any handler is done
in three steps:

(1) Initialization
gather arguments, check data types+mandatory, initialize the four
result members: data, units, args, mh.  In this step, any units-related
arguments in the request are stripped from the args dict and added to
the units dict with the resolved unit name (e.g. 'temperature' instead
of 'uT').  The remaining values in args will be used by process().

    rh = PropertyRequest(request)
    rh.data     # Initialized to an empty dictionary
    rh.units    # Loaded with any units found in the arguments
    rh.args     # Loaded with any non-units arguments
    rh.mh       # An initialized PMGIMessageHandler instance.

(2) Process units
Any units specified in the units dict are applied to the live PYroMat
installation.  Any not specified are reset to their default values and
recorded in the units dict, so all units will be reported every time.
This is a separate step because it is not always necessary.  For example,
informational calls have no need for units.

    rh.process_units()
    rh.units    # is now fully populated with the current units.
    rh.mh       # evaluates to True if an error occurred

(3) Process
The process() method is where the core of the request handling code goes.
This is where the relevant calculations are done.  Results should be
stored in the data member so they will be found by the output step.

    rh.process()
    rh.data     # is now populated with the request results
    rh.mh       # evaluates to True if an error occurred

(4) Output
The output() method assembles the contents of the data, units, args, and
mh members into a JSON-friendly dict.  Output does NOT do additional
post-processing like eliminating NaN values.  If necessary, that must be
handled in process().

    out = rh.output()
    # out now contains 'data', 'args', 'units', and 'message' entries

** UNITS **
In the initialization step, before the individual classes enforce their
unique requirements on the arguments, the prototype initializer strips
out any arguments that appear to be specifying a unit definition.

The simplest of these is an argument called 'units' set to a dictionary
that may contain any of the keys found in the valid_units dict.  These
are identical to the PYroMat config units, but with the leading 'unit_'
stripped.  Their values may be any recognized unit for that setting.

Because it requires a nested dict, this approach is probably only useful
in POST requests.  For GET requests, units may be specified one-at-a-
time using a shortened unit string.  A list of short unit specifiers
and their corresponding value in the units dictionary is:

    args    units
    ---------------------
    'uT'    'temperature'
    'uE'    'energy'
    'uMol'  'molar'
    'uMas'  'mass'
    'uM'    'matter'
    'uV'    'volume'
    'uP'    'pressure'
    'uF'    'force'
    'uL'    'length'
    'uTim'  'time'

Any units specifiers that are omitted will be loaded with their default
values when process_units() is executed.  If process_units() is not
called, the unit arguments are still separated out of the args dict, but
they are ignored.
"""

import flask
import pyromat as pm
import numpy as np
from flask import Flask, request
import sys

__version__ = '0.1'


# ### Helper functions
def toarray(a):
    try:
        return np.asarray(a, dtype=float)
    except ValueError:
        return np.asarray(a.split(','), dtype=float)


def tobool(a):
    if a.lower() in ['0', 'f', 'false']:
        return False
    return True


def ismultiphase(subst):
    """Test whether the PYroMat substance instance is a multi-phase model
    :param subst: A PYroMat substance instance
    :return True/False:
"""
    # Explicitly list the supported classes
    # This was my favorite of a few candidate algorithms.  It is quick,
    # it ensures that the instance will have the correct property
    # methods (which is really what you want to test for), and it will
    # be immune from creating strange new substance models in the future.
    testfor = ['mp1']
    for thisclass in testfor:
        if isinstance(subst, pm.reg.registry[thisclass]):
            return True
    return False
    # There are a few other candidate algorithms we could consider:
    # 1) We could test the substance's collection from its id string
    #    This has advantages if we ever add ideal liquid, solid, or
    #    other substance collections.
    # 2) We could test for a complete list of mandatory property methods
    #    This would ensure compatibility with the algorithm, but it
    #    would be slower.
    # 3) We could test for a single candidate property method (like ps)
    #    This isn't bad, but it's prone to problems if we aren't careful
    #    down the line.  However unlikely, it's possible that we'll make
    #    a new substance model with ps() that has a different meaning.


def json_friendly(unfriendly):
    """Clean up an output dictionary or list for output as JSON.
    friendly = json_friendly(unfriendly)

This function recursively checks each value of the list or dict (and all
child lists or dictionaries) for numpy data classes.  They are converted
to lists in place or (if possible) they are converted to scalars.

If the argument (unfriendly) is a list or dict, the same structure will
be returned, but with the appropriate modifications made internally.
If the argument is a numpy array, a list or scalar version will be
returned.  As a result, it is not necessary to catch the return value
unless a numpy array is passed explicitly.
"""

    # Handle numpy datatypes
    if isinstance(unfriendly, np.ndarray):
        if unfriendly.size == 1:
            if np.isinf(unfriendly):
                return "inf"
            elif np.isnan(unfriendly):
                return "nan"
            else:
                return np.asscalar(unfriendly)
        if any(np.isinf(unfriendly)):
            bad = np.isinf(unfriendly)
            lst = unfriendly.tolist()
            for i in np.where(bad)[0]:
                lst[i] = "inf"
            return lst
        if any(np.isnan(unfriendly)):
            bad = np.isnan(unfriendly)
            lst = unfriendly.tolist()
            for i in np.where(bad)[0]:
                lst[i] = "nan"
            return lst
        return unfriendly.tolist()
    # If this is a dict, recurse inside
    elif isinstance(unfriendly, dict):
        for name, value in unfriendly.items():
            unfriendly[name] = json_friendly(value)
    # If this is a list, recurse inside
    elif isinstance(unfriendly, list):
        for index, value in enumerate(unfriendly):
            unfriendly[index] = json_friendly(value)
    # Datatypes that aren't explicitly handled above are simply passed
    # through with no modification
    return unfriendly


def clean_nan(dirty, ignore=["cp", "cv", "gam"]):
    """Clean out nan values from a computed dict in place.
    result = clean_nan( dirty )

The PMGI has a number of use cases where arrays of equal length are
returned inside of a dictionary or list with the intention that they be
interpreted as varying together.  The PM property interface adds NaN
values at points that are out-of-bounds or otherwise illegal.  If any
arrays are found to have NaN values, those and the corresponding values
of all other arrays are removed. A list of ignored keys can be supplied.

On success, returns the number of NaN values found.

If the arrays are found to have incompatible shapes, -1 is returned.
"""

    # Prepare an iterator for the dirty dataset
    if isinstance(dirty, list):
        iterator = enumerate(dirty)
    elif isinstance(dirty, dict):
        iterator = dirty.items()

    # We'll keep track of the keys that need to be changed using
    # a "change_keys" list.
    change_keys = []

    # indices will eventually become a boolean array indicating which
    # of the values should be eliminated.
    indices = None
    for key, value in iterator:
        # If this is a numpy array, we need to check it
        if isinstance(value, np.ndarray):
            change_keys.append(key)
            ## If key in the ignore list, skip checking for nan
            if key in ignore:
                continue
            # If this is the first numpy array found, init indices
            if indices is None:
                indices = np.isnan(value)
            # If there are already indices, verify the shape
            elif indices.shape == value.shape:
                indices = np.logical_or(indices, np.isnan(value))
            else:
                return -1

    # There were no numpy arrays!
    if indices is None:
        return 0

    count = indices.sum()
    # If necessary, go back and remove NaN entries
    if count:
        indices = np.logical_not(indices)
        for key in change_keys:
            dirty[key] = dirty[key][indices]
    return count


def get_practical_limits(subst):
    """Return practical temperature and pressure boundaries for a substance
    Tmin,pmin,Tmax,pmax = get_practical_limits( subst )

Temeprature limits are always set based on the substance's Tlim() method,
but ideal gas substance models have no explicit pressure limits, and
most multi-phase minimum pressures are zero.  If the substance is a
multiphase instance with zero minimum pressure, 10% of the triple point
is used.  Ideal gas models use the pressure at T=Tmin,d=0.01 and T=Tmax,
d=1000.
"""
    if ismultiphase(subst):
        pmin, pmax = subst.plim()
        Tt, pt = subst.triple()
        if pmin == 0:
            pmin = 0.1 * pt
        Tmin, Tmax = subst.Tlim()
    else:
        Tmin, Tmax = subst.Tlim()
        pmin, pmax = np.array(
            [subst.p(T=Tmin, d=0.01), subst.p(T=Tmax, d=1000)]).flatten()

    peps_hi, peps_lo = 0.01 * pmax, pmin
    Teps = 0.001 * (Tmax - Tmin)

    return Tmin + Teps, pmin + peps_lo, Tmax - Teps, pmax - peps_hi


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
    Tmin, pmin, Tmax, pmax = get_practical_limits(subst)
    if multiphase:
        Tt, pt = subst.triple()

    if prop == 'p':
        vals = np.logspace(np.log10(pmin), np.log10(pmax), 10)
    elif prop == 'T':
        vals = np.linspace(Tmin, Tmax, 10)
    elif prop == 'x':
        vals = np.linspace(0.1, 0.9, 9)
    elif prop in ['v', 'd', 'h', 'e', 's']:
        pfn = getattr(subst, prop)
        try:  # Finding the low value can be flaky for some substances
            propmin = pfn(T=Tmin, p=pmax)
        except pm.utility.PMParamError:
            if multiphase:
                pfns = getattr(subst, prop + 's')
                propmin = pfns(T=Tt)[0]
            else:
                propmin = pfn(T=Tmin, p=pmin)
        propmax = pfn(T=Tmax, p=pmin)
        if prop == 'v':
            vals = np.logspace(np.log10(propmin), np.log10(propmax), 10)
        elif prop == 'd':  # Inverse of v means max and min flip
            vals = np.logspace(np.log10(propmax), np.log10(propmin), 10)
        else:
            vals = np.linspace(propmin, propmax, 10)
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
            try:
                lines.append(compute_iso_line(subst, n, scaling, **arg))
            except pm.utility.PMParamError:
                pass
        return lines

    # We have a single property, so compute the line

    # Compute the limit pressures and temperatures
    multiphase = hasattr(subst, 'Ts')
    Tmin, pmin, Tmax, pmax = get_practical_limits(subst)
    if multiphase:
        Tc, pc = subst.critical()
        Tt, pt = subst.triple()

    # The props for which we will plot against a T list
    if any(prop in kwargs for prop in ['p', 'd', 'v', 's', 'x']):

        # If quality, we stop at the crit pt
        if 'x' in kwargs:
            if multiphase:
                Tmax = Tc
            else:
                raise pm.utility.PMParamError('x cannot be computed for non-'
                                              'multiphase substances.')

        line_T = np.linspace(Tmin, Tmax, n).flatten()

        # We can insert the phase change points
        if multiphase and 'p' in kwargs and pc > kwargs['p'] > pt:
            Tsat = subst.Ts(p=kwargs['p'])
            i_insert = np.argmax(line_T > Tsat)

            line_T = np.insert(line_T, i_insert,
                               np.array([Tsat, Tsat]).flatten())
            x = -np.ones_like(line_T)
            x[line_T == Tsat] = np.array([0, 1])
            kwargs['x'] = x

        kwargs['T'] = line_T

    elif any(prop in kwargs for prop in ['h', 'e']):
        try:  # Finding the low value can be flaky for some substances
            dmax = subst.d(T=Tmin, p=pmax)
        except pm.utility.PMParamError:
            if multiphase:
                dmax = subst.ds(T=Tt)[0]
            else:
                dmax = subst.d(T=Tmin, p=pmin)
        dmin = subst.d(T=Tmax, p=pmin)
        line_d = np.logspace(np.log10(dmin), np.log10(dmax), n).flatten()
        # line_d = np.linspace(dmin, dmax, n)
        kwargs['d'] = line_d

    elif any(prop in kwargs for prop in ['T', 'h', 'e']):
        # ph & pe are going to be really slow, but what's better?

        line_p = np.logspace(np.log10(pmin), np.log10(pmax), n).flatten()

        # We can insert the phase change points
        if multiphase and 'T' in kwargs and Tc > kwargs['T'] > Tt:
            psat = subst.ps(T=kwargs['T'])
            i_insert = np.argmax(line_p > psat)

            line_p = np.insert(line_p, i_insert,
                               np.array([psat, psat]).flatten())
            x = -np.ones_like(line_p)
            x[line_p == psat] = np.array([1, 0])
            kwargs['x'] = x

        kwargs['p'] = line_p



    else:  # Should never arrive here without error
        raise pm.utility.PMParamError('property invalid')

    states = subst.state(**kwargs)

    return states


###
# Back-end helper/handler classes
#   These are responsible for automating some of the back-end tedium
#   associated with HTTP error handling and
###

class PMGIMessageHandler:
    """The Message Handler tracks errors, warnings, and accumulates messages
to the client machine that are registered throughout the request handling
process.

The PMGIMessageHandler class has three "private" attributes,
    _errorflag :: a boolean indicating whether an error occurred.
    _warnflag :: a boolean indicating whether a warning occurred.
    _messagestr :: the message text accumulated throughout the process

Methods used to interact with the MessageHandler instance are:
    error(message) :: Register an error with an appropriate message
    warn(message) :: Register a warning with an appropriate message
    message(message) :: Register a message without warning or error

Methods and functions may return a PMGIMessageHandler as part of their
normal operation.  PMGIMessageHandler instances may be combined in order
using addition or the incrementer,

mh1 = PMGIMessageHandler()
... some code that modifies mh1 ...
mh2 = some_function_that_returns_mh()
mh1 += mh2

At the conclusion of this code, mh1 includes the messages, warning, and
error states from both the function and the prior code.
"""

    def __init__(self, copy=None):
        self.clean()
        if isinstance(copy, PMGIMessageHandler):
            self._errorflag = bool(copy._errorflag)
            self._warnflag = bool(copy._warnflag)
            self._messagestr = str(copy._messagestr)
        elif isinstance(copy, str):
            self._messagestr = str(copy)
        elif copy is not None:
            raise Exception(
                'A PMGIMessageHandler was initialized with a unhandled type: ' + repr(
                    copy))

    def clean(self):
        """Clear the _errorflag, _warnflag, and _messagestr attributes
    mh.clear()

Clear should be called after the messages have been handled.
"""
        self._errorflag = False
        self._warnflag = False
        self._messagestr = ''

    def error(self, message, prefix='ERROR: ', newline=True):
        """Register an error, adding a prefix to its message, and appending a newline
    mh.error(message, prefix='ERROR: ', newline=True)

The message may be any string.  The prefix will be appended, so setting
it to an empty string disables this behavior.  A trailing newline is
always appended unless newline is set to False.

Calling this method sets the _errorflag to True.
"""
        self._errorflag = True
        self.message(message=message, prefix=prefix, newline=newline)

    def warn(self, message, prefix='WARNING: ', newline=True):
        """Register a warning, adding a prefix to its message, and appending a newline
    mh.warn(message, prefix='WARN: ', newline=True)

The message may be any string.  The prefix will be appended, so setting
it to an empty string disables this behavior.  A trailing newline is
always appended unless newline is set to False.

Calling this method sets the _warnflag to True.
"""
        self._warnflag = True
        self.message(message=message, prefix=prefix, newline=newline)

    def message(self, message, prefix='', newline=True):
        """Register a message without raising an error or warning
    mh.message(message, prefix='', newline=True)

The message method is like the error and warn methods, but there is no
prefix by default, and the _errorflag and _warnflag attributes are not
affected.
"""
        self._messagestr += prefix + message
        if newline:
            self._messagestr += '\n'

    def tojson(self):
        """Convert the PMGIMessageHandler instance to dict ready for JSON encoding
    out = mh.tojson()

out = {'message':mh._messagestr, 'error':mh._errorflag, 'warn:mh._warnflag}
"""
        return {'message': self._messagestr, 'error': self._errorflag,
                'warn': self._warnflag}

    def __add__(self, other):
        # Make a copy of self
        out = PMGIMessageHandler(self)
        # Use iadd to complete the addition
        out += other

    def __iadd__(self, other):
        self._errorflag = self._errorflag or other._errorflag
        self._warnflag = self._warnflag or other._warnflag
        self._messagestr = self._messagestr + other._messagestr

    def __bool__(self):
        return bool(self._errorflag)


###
# Custom request processing classes
#   These are designed to construct a JSON dictionary that will be used
#   by the HTML/JS on the client side to construct tables and plots.
###


class PMGIRequest:
    """The PYroMat Gateway Interface Request class

    pr = PMGIRequest( request )

The PMGIRequest class is a parent for the individual request handlers.
Handler instances are intended to manage the different kinds of requests
that come to the gateway interface while gracefully checking arguments
and failing gracefully with appropriate HTTP error conditions and
meaningful error messages.

request is the Flask request instance being processed, from which an
arguments dictionary is constructed. Since PMGIRequest is merely a
prototype for the individual request interfaces, it makes very few
assumptions about these arguments.

The PMGIRequest and its children have four important attributes:
    data    a dictionary containing JSON data resulting from the request
    mh      a PMGIMessageHandler instance for the request
    units   a dictionary containing units settings
    args    a dictionary containing the request's parameters

A request handling process should follow these steps:
(1) Init
    Each child class may define its own __init__ method, but it is
    recommended that the first line be a call to
    PMGIRequest.__init__(self, request).  This will automatically
    translate the GET/POST arguments into the args attribute dict, and it
    will automatically strip out units settings into the separate units
    attribute dict.

    Unit settings are either contained in an explicit 'units' dict or
    one-by-one in a "short" format.  Legal units classes and their
    supported values are enumerated in the legal_units attribute dict.
    Their equivalent short form for explicit definition using the GET
    method are mapped in the short_units attribute.

    Next, each child class should make a call to the require() method as
    a part of its own initialization.  This is where the child classes
    assert the rules about which request parameters are allowed,
    required, and their datatypes are asserted.

    Finally, each unit class should take any special steps that are
    unique to its request.  Many classes will not need to do anything
    additional.

(2) Process Units
    Not all child classes will need to perform this step, but calling
    process_units() will assert any units settings found in the
    arguments.  See above for how units are specified.

    Specified units will be asserted in the PYroMat configuration
    system.  Unspecified units will be returned to their default and
    written to the dictionary, so that they may be displayed by the live
    page.

(3) Process
    There is a generic process() method defined by the parent
    PMGIRequest prototype, but it does nothing.  Each child request
    handler should define its own process method, which is responsible
    for populating the data attribute.

    The process() method is expected to write to the data or the mh
    attributes, but it may only read from the units and args attributes.
    Messaging should be handled by the mh.error(), mh.warn(),
    and mh.message() methods.

    The get_substance() is a method provided by PMGIRequest that will
    probably be helpful in this step.

(4) Output
    The final output process should almost always be handled by the
    PMGIRequest.output() prototype method.  It assembles the data, args,
    units, and mh attributes into a standard JSON-compatible dictionary
    and returns it.  Using the same output method for all classes
    ensures that the PMGI output will always adopt a standard form, so
    custom output() methods should be avoided.

There are several methods that automate steps of this process.

get_substance()
    The get_substance() method is a wrapper around the PYroMat get()
    function, but it handles error logging in the mh attribute if a
    substance is not found or if some other error occurs.  Returns True
    on failure and False on success.

output()
    The output method automates step 4, and is described above and in
    its own in-line documentation.

process_units()
    The process_units() method is designed to automate step 2, and is
    described above.  It handles error logging and returns True on
    failure and False on success.
"""

    def __init__(self, request):
        # Initialize the four parts of the output
        self.mh = PMGIMessageHandler()
        self.units = {}
        self.data = {}
        # Read in the request data to an args dict
        if request.method == 'POST':
            self.args = dict(request.json)
        elif request.method == 'GET':
            self.args = dict(request.args)
        else:
            self.args = {}

        # Build legal unit dict
        self.valid_units = {
            'temperature': list(pm.units.temperature.get()),
            'energy': list(pm.units.energy.get()),
            'molar': list(pm.units.molar.get()),
            'mass': list(pm.units.mass.get()),
            'matter': list(pm.units.mass.get()) + list(pm.units.molar.get()),
            'volume': list(pm.units.volume.get()),
            'pressure': list(pm.units.pressure.get()),
            'force': list(pm.units.force.get()),
            'length': list(pm.units.length.get()),
            'time': list(pm.units.time.get())
        }
        # The short units map abbreviated unit strings intended for the
        # GET interface
        self.short_units = {
            'uT': 'temperature',
            'uE': 'energy',
            'uMol': 'molar',
            'uMas': 'mass',
            'uM': 'matter',
            'uV': 'volume',
            'uP': 'pressure',
            'uF': 'force',
            'uL': 'length',
            'uTim': 'time'
        }

        # Process any units specifiers - strip them from the args
        # dict as they are discovered.
        # Look for a nested "units" dict
        if 'units' in self.args:
            # Pop out the units dictionary
            self.units = self.args.pop('units')

            if not isinstance(self.units, dict):
                self.mh.error('The units argument was not a dictionary.')
                return True
        # If the units dict was not found, look for any short unit
        # specifiers in the root arguments - probably for GET
        else:
            # We'll be changing the contents of args as we iterate, so
            # we need to iterate on a copy of the argument keys
            for shortunit in list(self.args.keys()):
                # If this is a short unit, pop it out of args
                # and add its long version to the newunits dict
                if shortunit in self.short_units:
                    longunit = self.short_units[shortunit]
                    self.units[longunit] = self.args.pop(shortunit)

        # Finally, test the units for correctness as we read them into
        # the live units dict
        for unit, value in self.units.items():
            # Next, retrieve the legal values. If none are found, this
            # is not a valid unit specifier string.
            legal_values = self.valid_units.get(unit)
            if legal_values is None:
                self.mh.error('Unit not recognized: ' + str(unit))
            # Is the assigned unit legal?
            elif value not in self.valid_units[unit]:
                self.mh.error('Unit (' + str(
                    unit) + ') was set to unrecognized value: ' + str(value))

    def require(self, types, mandatory):
        """REQUIRE - enforce rules about the request arguments
    require(types, mandatory)

The require() method is intended to be called in each child request
class to enforce that all arguments are recognized, a valid datatype,
and that all mandatory arguments are present.  This method writes to
the class's mh attribute automatically if errors or warnings are
encountered.

types       A dictionary of arguments and their types
mandatory   A list, set, or tuple of required argument names

Each keyword in TYPES corresponds to an argument that is allowed.  The
corresponding value in the dictionary must be a class or callable that
will be used to condition the argument's value.  For example,
specifying:
    types = {'teamname': str, 'players': int, 'color': str}
defines three optional arguments and their types.  More complicated
requirements or conditioning can be applied by assigning custom
types or functions instead of existing types.

Once defined in TYPES, an argument can be made mandatory by including
its name in the MANDATORY list.

Returns True if an error occurs and False otherwise.  Messages are
logged appropriately in the mh attribute.
"""
        # Make a copy of the mandatory set.  We'll be keeping track!
        mandatory = set(mandatory)
        # Loop through the items
        for name, value in self.args.items():
            # Is this a recognized argument?
            if name not in types:
                self.mh.error(f'Unrecognized argument: {name}')
                return True
            # If the argument is known
            try:
                self.args[name] = types[name](value)  # Cast to type
            except:
                self.mh.error(f'Invalid argument: {name}={value}')
                return True
            # If the argument is mandatory, check it off the list
            if name in mandatory:
                mandatory.remove(name)
        # Are there missing arguments?
        if mandatory:
            self.mh.error('Missing mandatory arguments: ', newline=False)
            prefix = ''
            for name in mandatory:
                self.mh.message(name, prefix=prefix, newline=False)
                prefix = ', '
            # Force a newline
            self.mh.message('')
            return True
        return False

    def process_units(self):
        """Assign the units discovered in the arguments to PYroMat's settings
    process_units()

Uses the dict stored in the units attribute to determine which (if any)
units need to be changed from the default.  If units is empty, no changes
are made.

Units specified in the units dict are modified in the PYroMat system.
Other units found in the PMyroMat system are recorded in the units dict
to record the system's units status.

Returns True in the event of an error.  On success, returns False.
"""
        if self.mh:
            self.mh.message('Unit processing aborted due to an error.')
            return True
        # Loop through all possible parameters, and only work on the
        # units.
        for param in pm.config:
            if param.startswith('unit_'):
                unit = param[5:]
                # If the unit was specified in the configuration
                if unit in self.units:
                    try:
                        pm.config[param] = self.units[unit]
                    except:
                        self.mh.error('Failed to set the units as configured.')
                        self.mh.message(repr(sys.exc_info()[1]))
                        return True
                # If it was not specified, return it to its default value
                # and record it for the output record
                else:
                    pm.config.restore_default(param)
                    self.units[unit] = pm.config[param]
        return False

    def get_substance(self, idstr):
        """Wrapper function for pm.get() that registers appropriate error messages
    substance = get_substance(idstr)

The idstr is the ID string used by get().
"""
        substance = None
        try:
            substance = pm.get(idstr)
        except pm.utility.PMParamError:
            self.mh.error('Substance not found: ' + str(idstr))
        except:
            self.mh.error(
                'There was an unexpected error retrieving substance: ' + str(
                    idstr))
            self.mh.message(repr(sys.exc_info()[1]))
        return substance

    def process(self):
        """This is a prototype for a request process method.
    pr.process()

The process method is responsible for populating the data attribute.
"""
        # If there was an error, abort
        if self.mh:
            self.mh.message('Aborted processing due to an error')
            return True

        # interesting code for generating data here...
        self.data = {}

        return False

    def output(self):
        """Generate the serializable output of the process request.
"""
        return {
            'data': json_friendly(self.data),
            'message': self.mh.tojson(),
            'units': self.units,
            'args': json_friendly(self.args)
        }


class SubstanceRequest(PMGIRequest):
    """This class handles substance metadata requests
"""
    inprops = ['e', 'h', 's', 'T', 'p', 'd', 'v', 'x']
    outprops = inprops + ['cp', 'cv', 'gam']

    def __init__(self, args):
        PMGIRequest.__init__(self, args)
        self.require(types={
            'id': str},
            mandatory=['id'])

    def process(self):
        # If there was an error, abort the processing
        if self.mh:
            self.mh.message('Processing aborted due to error.')
            return True

        # Copy the args and pop out the id entry
        # Everything that's left will be arguments to the state method
        args = self.args.copy()
        subst = self.get_substance(args.pop('id'))
        if subst is None:
            return True

        try:
            self.data['id'] = subst.data['id']
            self.data['mw'] = subst.mw()
            self.data['names'] = subst.names()
            self.data['col'] = subst.collection()
            self.data['cls'] = subst.pmclass()
            self.data['inchi'] = subst.inchi()
            self.data['casid'] = subst.casid()
            self.data['atoms'] = subst.atoms()
            self.data['doc'] = subst.data.get('doc')
            if self.data['cls'] in ['mp1']:
                self.data['Tc'], self.data['pc'], self.data[
                    'dc'] = subst.critical(density=True)
                self.data['Tt'], self.data['pt'] = subst.triple()

            self.data['inprops'] = self.inprops
            self.data['outprops'] = self.outprops
            for prop in self.outprops:
                if not hasattr(subst, prop):
                    self.data['outprops'].remove(prop)
                    if prop in self.data['inprops']:
                        self.data['inprops'].remove(prop)

        except pm.utility.PMParamError:
            self.mh.error('Failed to generate parameter set.')
            self.mh.message(repr(sys.exc_info()[1]))
            return True

        return False


class PropertyRequest(PMGIRequest):
    """
    This class will handle requests for properties at a fixed state or states.
    """

    def __init__(self, args):
        # Clean initialization
        PMGIRequest.__init__(self, args)
        # Process the arguments
        self.require(types={
            's': toarray,
            'h': toarray,
            'e': toarray,
            'T': toarray,
            'p': toarray,
            'd': toarray,
            'v': toarray,
            'x': toarray,
            'id': str},
            mandatory=['id'])

    def process(self):
        """Process the request
        This method is responsible for populating the "out" member dict with
        correctly formatted data that can be returned as a JSON object.
        """
        # If there was an error, abort the processing
        if self.mh:
            self.mh.message('Processing aborted due to error.')
            return True

        # Copy the args and pop out the id entry
        # Everything that's left will be arguments to the state method
        args = self.args.copy()
        subst = self.get_substance(args.pop('id'))
        if subst is None:
            return True

        try:
            self.data = subst.state(**args)
        except (pm.utility.PMParamError, pm.utility.PMAnalysisError):
            self.mh.error('Failed to generate parameter set.')
            self.mh.message(repr(sys.exc_info()[1]))
            return True

        return False


class IsolineRequest(PMGIRequest):
    """
    This class will handle requests for an isoline
    """

    def __init__(self, args):
        # Clean initialization
        PMGIRequest.__init__(self, args)

        self.require(types={
            's': toarray,
            'h': toarray,
            'e': toarray,
            'T': toarray,
            'p': toarray,
            'd': toarray,
            'v': toarray,
            'x': toarray,
            'default': str,
            'id': str},
            mandatory=['id'])

    def process(self):
        """Process the request
        This method is responsible for populating the "out" member dict with
        correctly formatted data that can be returned as a JSON object.
        """
        # If there was an error, abort the processing
        if self.mh:
            self.mh.message('Processing aborted due to error.')
            return True

        args = self.args.copy()
        # Leave only the property arguments
        subst = self.get_substance(args.pop('id'))
        if subst is None:
            return True

        try:
            self.data['data'] = compute_iso_line(subst, n=50, **args)
            if isinstance(self.data['data'], list):
                for row in self.data['data']:
                    clean_nan(row)  # TODO Kludge clean_nan not working on list
            else:
                clean_nan(self.data['data'])
        except (pm.utility.PMParamError, pm.utility.PMAnalysisError) as e:
            self.mh.error('Failed to generate isoline.')
            self.mh.message(repr(sys.exc_info()[1]))
            return True


class SaturationRequest(PMGIRequest):
    """
    This class will handle requests for saturation properties.
    """

    def __init__(self, request):
        # Clean initialization
        PMGIRequest.__init__(self, request)
        # Process the arguments
        self.require(
            types={
                'T': toarray,
                'p': toarray,
                'id': str
            },
            mandatory=['id'])

    def process(self):
        """Process the request
        This method is responsible for populating the "out" member dict with
        correctly formatted data that can be returned as a JSON object.

        If no property is specified, the entire steam dome will be returned
        """
        # If there was an error, abort the processing
        if self.mh:
            self.mh.message('Processing aborted due to error.')
            return True

        # Copy the args and pop out the id entry
        # Everything that's left will be arguments to the state method
        args = self.args.copy()
        subst = self.get_substance(args.pop('id'))
        # get_substance() handles error logging for us - we only need to
        # return True if it fails.
        if subst is None:
            return True
        # Throw an error if the substance is not multi-phase
        if not ismultiphase(subst):
            self.mh.error(
                'Substance was not in the multi-phase collection: ' + repr(
                    subst))
            return True

        ## This segment of code is strictly responsible for generating
        # an array of temperature values to use

        # If there are no arguments, then generate a default set of
        # values
        if len(args) == 0:
            Tc, pc = subst.critical()
            Tt, pt = subst.triple()
            ep = (Tc - Tt) * .001
            Ts = np.linspace(Tt + ep, Tc - ep, 31)
        # Test for over-defined states
        elif len(args) > 1:
            self.mh.error('Saturation properties require only one argument.')
            return True
        # If T is specified, this is easy
        elif 'T' in args:
            Ts = args['T']
        # If p is specified, we'll need to calculate T
        elif 'p' in args:
            try:
                Ts = subst.Ts(p=args['p'])
            except (pm.utility.PMParamError, pm.utility.PMAnalysisError) as e:
                self.mh.error(
                    'Failed to obtain temperature at the pressure(s) provided.')
                self.mh.message(repr(e))
                return True
        # This should never happen - fail loudly.
        else:
            self.mh.error(
                'Unhandled SaturationRequest error! Please file a bug report.')
            return True

        # OK, we've got Ts - go calculate the state
        try:
            dsL, dsV = subst.ds(T=Ts)
            self.data['liquid'] = subst.state(T=Ts, d=dsL)
            self.data['vapor'] = subst.state(T=Ts, d=dsV)
            # Throw away the liquid pressure - it is not numerically correct.
            self.data['liquid']['p'] = self.data['vapor']['p']
        except (pm.utility.PMParamError, pm.utility.PMAnalysisError) as e:
            self.mh.error(
                'Failed to evaluate saturation properties at the state(s) provided.')
            self.mh.message(repr(e))
            return True

        count = clean_nan(self.data['liquid']) \
                + clean_nan(self.data['vapor'])
        if count:
            self.mh.warn(
                'Encountered states that were out of bounds for this substance model.')

        return False


class InfoRequest(PMGIRequest):
    """
This class will handle generic info requests about pyromat data
"""

    def __init__(self, args):
        PMGIRequest.__init__(self, args)

        self.require(types={
            'substances': tobool,
            'legalunits': tobool,
            'versions': tobool}, mandatory=[])

    def process(self):
        """Process the request
This method is responsible for populating the "out" member dict with
correctly formatted data that can be returned as a JSON object.
"""
        # If there was an error, abort
        if self.mh:
            self.mh.message('Aborted processing due to an error')
            return True

        # Should we obtain the list of substances?
        subst_flag = self.args.get('substances')
        subst_dict = {}
        # If substances was not set or was set to True
        if subst_flag is None or subst_flag:
            for idstr, subst in pm.dat.data.items():
                subst_dict[idstr] = {
                    'cls': subst.pmclass(),
                    'col': subst.collection(),
                    'nam': subst.names(),
                    'mw': subst.mw()}
        self.data['substances'] = subst_dict

        # Should we obtain the list of valid units?
        units_flag = self.args.get('legalunits')
        units_dict = {}
        if units_flag is None or units_flag:
            units_dict = self.valid_units.copy()
        self.data['legalunits'] = units_dict

        # Should we obtain the version information?
        version_flag = self.args.get('versions')
        version_dict = {}
        if version_flag is None or version_flag:
            version_dict = {
                'python': sys.version.split()[0],
                'flask': flask.__version__,
                'pyromat': pm.config['version'],
                'pmgi': __version__,
                'numpy': np.version.full_version,
            }
        self.data['versions'] = version_dict


############################
# Define the URL interface #
############################
app = Flask(__name__)


# Flask will see the route as relative to the apache WSGI alias
# The intent is that the WSGI root be set to pyromat.org/pmgi, so that
# will redirect here - to root.


# Sitemap:
# /substance
#
#   Return meta information about a specific substance
#
# /state
#   Return property information at a state or array of states
#
# /saturation
#   Return property information along a saturation line
#
# /isoline
#   Return property information while holding a single property constant
#
# /info
#   Return meta information about the active installation of PYroMat

@app.route('/subst', methods=['POST', 'GET'])
def substance():
    sr = SubstanceRequest(request)
    sr.process_units()
    sr.process()
    return sr.output(), 200


# The root pmgi accepts property requests.
@app.route('/state', methods=['POST', 'GET'])
def state():
    pr = PropertyRequest(request)
    pr.process_units()
    pr.process()

    return pr.output(), 200


# The saturation route computes saturation points or the steam dome
@app.route('/saturation', methods=['POST', 'GET'])
def saturation():
    sr = SaturationRequest(request)
    sr.process_units()
    sr.process()
    return sr.output(), 200


# The isoline route computes isolines
@app.route('/isoline', methods=['POST', 'GET'])
def isoline():
    # Read in the request data to an args dict
    isr = IsolineRequest(request)
    isr.process_units()
    isr.process()
    return isr.output(), 200


# The info pmgi will return the results of queries (e.g. substance search)
@app.route('/info', methods=['POST', 'GET'])
def info():
    ir = InfoRequest(request)
    ir.process_units()
    ir.process()
    return ir.output(), 200


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
