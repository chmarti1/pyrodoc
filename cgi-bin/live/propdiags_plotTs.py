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


species, up, uT, uE, uM, uV = pmcgi.argparse([
        ('id'),
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

# We don't know where the state will be exactly
sz = (11,8.25)
with nostdout():
    ax = pmplot.Ts(F,size=sz,display=False)
f = ax.get_figure()

# Instead of saving to a file, write directly to stdout!
print("Content-type: image/png")
print("")
f.savefig(sys.stdout, format='png')

