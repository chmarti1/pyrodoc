#!/usr/bin/python
#
#   Isobar plot generator

import matplotlib as mpl

# It is vital to set the matplotlib interface to one without a display
# BEFORE loading pyplot!  This makes things work behind Apache.
mpl.use('Agg')
import matplotlib.pyplot as plt
import pmcgi
import pyromat as pm
import pyroplot_local as pmplot
import numpy as np

import contextlib
import io
import sys

#Silence STDOUT warnings
#https://stackoverflow.com/questions/2828953/silence-the-stdout-of-a-function-in-python-without-trashing-sys-stdout-and-resto
@contextlib.contextmanager
def nostdout():
    save_stdout = sys.stdout
    sys.stdout = io.BytesIO()
    yield
    sys.stdout = save_stdout


species, type, plin, Tlin, vlin, hlin, slin, up, uT, uE, uM, uV = pmcgi.argparse([
        ('id'),
        ('type',str,'Ts'),
        ('plin',str,'false'),
        ('Tlin',str,'false'),
        ('vlin',str,'false'),
        ('hlin',str,'false'),
        ('slin',str,'false'),
        ('up'),
        ('uT'),
        ('uE'),
        ('uM'),
        ('uV') ])


# Apply the units
pm.config['unit_temperature'] = uT
pm.config['unit_pressure'] = up
pm.config['unit_matter'] = uM
pm.config['unit_energy'] = uE
pm.config['unit_volume'] = uV

this = pm.get(species)

# Calculate the states
F = pm.get(species)

if plin == 'true':
    plines = None
else:
    plines = []

if Tlin == 'true':
    Tlines = None
else:
    Tlines = []

if vlin == 'true':
    vlines = None
else:
    vlines = []

if hlin == 'true':
    hlines = None
else:
    hlines = []

if slin == 'true':
    slines = None
else:
    slines = []

# We don't know where the state will be exactly
sz = (11,8.25)

with nostdout():
    if type=='Ts':
        ax = pmplot.Ts(F, plines=plines, vlines=vlines, hlines=hlines, size=sz, display=False)
    elif type=='Tv':
        ax = pmplot.Tv(F, plines=plines, slines=slines, hlines=hlines, size=sz, display=False)
    elif type=='pv':
        ax = pmplot.pv(F, Tlines=Tlines, slines=slines, hlines=hlines, size=sz, display=False)
f = ax.get_figure()


from matplotlib.backends.backend_pdf import PdfPages
pp = PdfPages('test.pdf')
pp.savefig(f)
pp.close()


# Instead of saving to a file, write directly to stdout!
print("Content-type: application/octet-stream")
print("Content-Disposition: attachment; filename=test.pdf")
print()

from shutil import copyfileobj
with open('test.pdf','rb') as zipfile:
    copyfileobj(zipfile, sys.stdout.buffer)


