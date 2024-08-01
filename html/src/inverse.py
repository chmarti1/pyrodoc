#!/usr/bin/python3
import pyromat as pm
from scipy import optimize as op


# Residual functions are used to calculate the "error" between a guess 
# and the target value.  Here, we calculate enthalpy at a guess 
# temperature and the target quality.  The difference between that value
# and the target enthalpy is the "error."
def residual(T,subst,h,x):
    return h-subst.h(T=T, x=x)
    
# This is a quick-and-dirty function for calculating temperature from 
# enthalpy and quality.  I hope this is helpful, and I hope it also
# demonstrates why PYroMat doesn't offer this functionality natively.
def T(subst,h,x,T0=None):
    """Calculate temperature from enthalpy and quality
    T = T(subst, h, x)
    
subst   PYroMat mp1 multi-phase instance
h       enthalpy in currently configured units
x       quality

This algorithm is not strictly sound because T(h,x) is not a function. 
For high values of quality, the curve doubles back on itself, giving
two possible solutions.  This code is constructed in an attempt (no
promises!) to always calculate the lower of the two temperatures.
"""
    # Make the initial guess closer to the triple point.
    # That should help keep us clear of the monkey business near the
    # critical point.
    if T0 is None:
        T0 = 0.9 * subst.triple()[0] + 0.1 * subst.critical()[0]
    # The Scipy package offers advanced numerical inversion routines
    # This is one of the most basic.
    return op.newton(residual, T0, args=(subst,h,x))
    
if __name__ == '__main__':
    pm.config['unit_temperature'] = 'K'
    subst = pm.get('mp.H2O')
    T_true = 450.
    x = 0.85
    h = subst.h(T=T_true,x=x)
    T_test = T(subst, h, x)
    
    print('Units are as currently configured in pm.config')
    print('True T        : ', T_true)
    print('Quality       : ', x)
    print('Enthalpy      : ', h)
    print('T(h,x)        : ', T_test)
    T_test = T(subst, h, x, T0 = 600.)
    print('T(h,x,T0=600) : ', T_test)
    T_test = T(subst, h, x, T0 = 575.)  # <=== BREAKS!!!
    print('T(h,x,T0=575) : ', T_test)
    # When I run this, I get:
    # Units are as currently configured in pm.config
    # True T (K)    :  450.0
    # Quality       :  0.85
    # Enthalpy      :  [2470.65102748]
    # T(h,x)        :  [450.]
    # T(h,x,T0=600) :  [612.25939454]
    # Traceback (most recent call last):
    # File "./inverse.py", line 52, in <module>
    #  ...

    # Note that the initial guess matters quite a bit, and it can even 
    # cause numerical failure if it is near the "flat" part of the curve.



    
