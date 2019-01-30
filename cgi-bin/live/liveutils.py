import pmcgi
import os
import pyromat as pm
import contextlib
import io
import sys
import numpy as np
import pyromat.solve as pmsolve

def perror(page,errtext,line):
    page.insert("""<div class="error">ERROR<br>"""+errtext,(line, 0))
    page.write()
    exit()

def unitsetup(page,up,uT,uE,uM,uV,unitline):
    # Build the available units menu based on the user's selections
    # Pressure
    text = pmcgi.html_select(
        pm.units.pressure.get(), selected=up, select=False)
    page.insert(text, (unitline, 55), wait=True)
    # Temperature
    text = pmcgi.html_select(
        pm.units.temperature.get(), selected=uT, select=False)
    page.insert(text, (unitline + 1, 58), wait=True)
    # Energy
    text = pmcgi.html_select(
        pm.units.energy.get(), selected=uE, select=False)
    page.insert(text, (unitline + 2, 53), wait=True)
    # Matter
    text = pmcgi.html_select(
        pm.units.mass.get() + pm.units.molar.get(),
        selected=uM, select=False)
    page.insert(text, (unitline + 3, 53), wait=True)
    # Volume
    text = pmcgi.html_select(
        pm.units.volume.get(), selected=uV, select=False)
    page.insert(text, (unitline + 4, 53), wait=True)

def setspeciesselect(page,species,inputline,column):
    # Build the substance menu
    # Include all multiphase collection members
    values = []
    for name in pm.dat.data:
        if name.startswith('mp.'):
            values.append(name)
    page.insert(
        pmcgi.html_select(values, select=False, selected=species),
        (inputline,column),
        wait=True)

def setinputs(page,settings,columns,inputline):
    i=0
    for setting,column in zip(settings,columns):
        page.insert(setting,(inputline+i,column),wait=True)
        i+=1


#Silence STDOUT warnings
#https://stackoverflow.com/questions/2828953/silence-the-stdout-of-a-function-in-python-without-trashing-sys-stdout-and-resto
@contextlib.contextmanager
def nostdout():
    save_stdout = sys.stdout
    sys.stdout = io.BytesIO()
    yield
    sys.stdout = save_stdout