"""PYroPlot: The PYroMat plotting module

ts()        Temperature-entropy diagrams
ph()        Pressure-enthalpy diagrams

"""

import matplotlib.pyplot as plt
import matplotlib.figure
import numpy as np
import pyromat as pm
import pyromat.solve as pmsolve


config = {
    'sat_color':'k',
    'sat_width':2,
    'sat_style':'-',
    'p_color':[1.0,0.5,0.5],
    'p_width':1,
    'p_style':'-',
    'd_color':[0.5,0.5,1.0],
    'd_width':1,
    'd_style':'-',
    'h_color':[0.3,0.6,0.3],
    'h_width':1,
    'h_style':'-',
    's_color': [0.5, 0.5, 1.0],
    's_width': 1,
    's_style': '-',
    'size': (8,6)
}

def _slope_ratio(axis, scaling='linear'):
    """
    Get the ratio of the mathematical derivative to the geometric
    slope on any given figure axis.

    Result can be used as: figure_slope = math_slope * ratio

    :param figure: the figure that the plot exists on
    :param axis:  the axis that the plot exists on
    :param scaling: one of 'linear','logx','logy','loglog'
    :return: the ratio to be used in the formula
    """

    figure = axis.get_figure()

    # Ratio of plot axes
    size = figure.get_size_inches() * figure.dpi
    w = size[0]
    h = size[1]
    origin = axis.get_position()
    originx_pct = origin.get_points()[0][0]
    originy_pct = origin.get_points()[0][1]
    maxx_pct = origin.get_points()[1][0]
    maxy_pct = origin.get_points()[1][1]
    xlim_low = axis.get_xlim()[0]
    xlim_hi = axis.get_xlim()[1]
    ylim_low = axis.get_ylim()[0]
    ylim_hi = axis.get_ylim()[1]
    xpix = w * (maxx_pct - originx_pct)
    ypix = h * (maxy_pct - originy_pct)
    if scaling == 'linear':
        xrange = xlim_hi - xlim_low
        yrange = ylim_hi - ylim_low
    elif scaling == 'logx':
        xrange = np.log10(xlim_hi / xlim_low)
        yrange = ylim_hi - ylim_low
    elif scaling == 'logy':
        xrange = xlim_hi - xlim_low
        yrange = np.log10(ylim_hi / ylim_low)
    elif scaling == 'loglog':
        xrange = np.log10(xlim_hi / xlim_low)
        yrange = np.log10(ylim_hi / ylim_low)
    else:
        raise ValueError("Parameter 'scaling': must be one of 'linear','logx','logy','loglog'.")
    r = (xrange / xpix) / (yrange / ypix)  # dydx*r where r= (xrange/xpix)/(yrange/ypix)
    return r

def _get_slope(x, y, pct, delta=None, scaling='linear'):
    """
    Get the slope of a line from a vector of y & x, at a given percentage through the vector.
    Use an index difference of delta
    :param x: a vector of x values
    :param y: a vector of y values
    :param pct: the fraction of the vector's length at which to compute the label position and derivative
    :param delta: the fraction of the vector's length to use for the numerical derivative spacing
    :param scaling: string, one of 'linear', 'logx', 'logy','loglog'
    :return: a dict with keys 'x','y','dydx', representing the x,y position of the label, and its slope
    """

    if len(y) != len(x):
        raise ValueError('x and y vectors must have the same length().')

    length = len(y) - 1 #the full range of indices runs from 0:length
    position_index = int(np.floor(pct*length)) #the index that we'll use to position the label

    if delta is not None:
        dx = np.max((np.floor(delta*(length)),1)) #calculate the dx for the derivative, with a minimum of 1
    else:
        dx = 1 #if delta unspecified, use a value of 1

    #calculate the indices for the derivative, coercing them within the length of the vectors
    firsti = int(np.max((0,position_index-dx)))
    lasti = int(np.min((firsti+dx,length)))

    #Calculate the derivative differently based on the plot type
    if scaling == 'loglog':
        dydx = np.log10(y[lasti] / y[firsti]) / np.log10(x[lasti] / x[firsti])
    elif scaling == 'logx':
        dydx = (y[lasti] - y[firsti]) / np.log10(x[lasti] / x[firsti])
    elif scaling == 'logy':
        dydx = np.log10(y[lasti] / y[firsti]) / (x[lasti] - x[firsti])
    elif scaling == 'linear':
        dydx = (y[lasti] - y[firsti]) / (x[lasti] - x[firsti])

    labeldata = {}
    labeldata['x'] = x[position_index]
    labeldata['y'] = y[position_index]
    labeldata['dydx'] = dydx

    return labeldata

def _interval(start, stop, count, inc=[1,2,5]):
    """Auto-generate conveniently spaced values in a range
    array = _interval(start, stop, count)
    
Generates an array of approximately uniformly spaced values beginning 
after start, and stopping before stop.  Unlike arange() or linspace(),
this function chooses values that are rounded to a nearest convenient 
interval.  This is commonly done for plotting.

The optional 'inc' parameter indicates the intervals that may be used
in any given decade.  They should be values larger than or equal to 1
and smaller than 10.  By default, inc=[1,2,5], which indicates that 
valid step sizes might be .01, .02, .05, .1, .2, .5, 1, 2, 5, 10, 20, 50
etc... 

To produce elegantly roundable numbers, the start value will be rounded
up to the nearest integer multiple of the selected incrementer.
"""
    # Calculate an increment that is the next largerst value in inc
    # scaled to the relevant decade
    dx = abs(stop-start) / count
    power = np.floor(np.log10(dx))
    dx /= 10**power
    inc.sort(reverse=True)
    for ii in inc:
        if ii<=dx:
            break
    dx = ii * 10**power
    
    # Round to the nearest incrementer
    start = dx * np.ceil(start / dx)
    return np.arange(start, stop, dx)
    
def _log_interval(start, stop, count, inc=[1,2,5]):
    """Auto-generate conveniently spaced values in a range
    array = _log_interval(start, stop, count)
    
Generates an array of approximately count values beginning after start, 
and stopping before stop.  Just like _interval(), this function does not
strictly respect the start, stop, or count parameters, but rounds to
the nearest conveniently represented decimal value. 

Unlike _interval(), _log_interval() adjusts the incrementer as the 
series progresses, so that it will always match the decade of the 
current value.

The optional 'inc' parameter indicates the intervals that may be used
in any given decade.  They should be values larger than or equal to 1
and smaller than 10.  By default, inc=[1,2,5], which indicates that 
valid step sizes might be .01, .02, .05, .1, .2, .5, 1, 2, 5, 10, 20, 50
etc... 

To produce elegantly roundable numbers, the start value will be rounded
up to the nearest integer multiple of the selected incrementer.
"""
    inc = np.asarray(inc)
    # transform the problem to a log-space
    log_start = np.log(start)
    log_stop = np.log(stop)
    log_dx = abs(log_stop - log_start) / count
    # produce an evenly spaced logarithmic series
    out = np.exp(np.arange(log_start, log_stop, log_dx))
    dx = out * log_dx
    for ii in range(out.size):
        # Calculate a nominal spacing
        dx = np.abs(out[ii] * log_dx)
        power = np.floor(np.log10(dx))
        dx /= 10**power
        # Adjust it to the nearest inc value
        dx = inc[np.argmin(np.abs(inc-dx))] * 10 ** power
        # Round out to the nearest integer multiple of the dx value
        out[ii] = dx * np.round(out[ii]/dx)
        
    # eliminate any points outside of start and stop
    out = out[np.logical_and(
            out <= max(start,stop),
            out >= min(start,stop)
            )]
    return out


def _dlines(mpobj,n=10):
    """Returns the default density lines for a given mpobject"""
    Tc,pc,dc = mpobj.critical(density=True)
    dlim = [dc / 1000., 2 * dc]
    vlim = [1/dlim[1],1/dlim[0]]
    #DLINES = np.flip(_log_interval(dlim[0], dlim[1], n, [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]), 0)
    DLINES = np.flip(1/np.logspace(-3,1,n))
    DLINES = np.flip(1/_log_interval(vlim[0], vlim[1], n, [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]),0)
    return DLINES

def _vlines(mpobj,n=10):
    Tc, pc, dc = mpobj.critical(density=True)
    dlim = [dc / 1000., 2 * dc]
    vlim = [1 / dlim[1], 1 / dlim[0]]
    VLINES = _log_interval(vlim[0], vlim[1], n, [0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
    VLINES = _log_interval(0.001, 10, n)
    return VLINES

def _plines(mpobj, n=10):
    """Returns the default pressure lines for a given mpobject"""
    plim = mpobj.plim()
    Tt,pt = mpobj.triple()
    # Force plim to be greater than pt
    plim[0] = max(pt, plim[0])
    PLINES = _log_interval(plim[0], plim[1], n)
    return PLINES

def _Tlines(mpobj, n=5):
    """Returns the default temperature lines for a given mpobject"""
    Tlim = mpobj.Tlim()
    TLINES = _interval(Tlim[0], Tlim[1], n)
    return TLINES

def _hlines(mpobj, n=15):
    """Returns the default enthalpy lines for a given mpobject"""
    plim = mpobj.plim()
    Tt,pt = mpobj.triple()
    # Force plim to be greater than pt
    plim[0] = max(pt, plim[0])
    Tlim = mpobj.Tlim()
    hlim = [mpobj.h(T=1.05 * Tlim[0], p=0.95 * plim[1]), mpobj.h(T=0.95 * Tlim[1], p=0.95 * plim[1])]
    #HLINES = np.linspace(hlim[0], hlim[1], n)
    HLINES = _interval(hlim[0], hlim[1], n)
    return HLINES

def _slines(mpobj,n=15):
    """Returns the default entropy lines for a given mpobject"""
    plim = mpobj.plim()
    Tt,pt = mpobj.triple()
    # Force plim to be greater than pt
    plim[0] = max(pt, plim[0])
    Tlim = mpobj.Tlim()
    slim = [mpobj.s(T=1.05 * Tlim[0], p= 0.99* plim[1]), mpobj.s(T=0.95 * Tlim[1], p=1.05 * plim[0])]
    SLINES = np.linspace(slim[0], slim[1], n)
    #SLINES = _interval(slim[0], slim[1], n)
    return SLINES

def _labellines(axis,LINES, LABELS,scalingratio,unitlabel,numformat,location,color):
    """
    Place labels on a given line
    :param axis: The axis object
    :param LINES: The list of lines that we're operating on
    :param LABELS: The dict of labels for those lines (dict with keys = values in LINES)
    :param scalingratio: The numbers to pixels scaling ratio
    :param unitlabel: String unitlabel applied to first and last values
    :param numformat: number formatting string applied to determine the value in LINES
    :param location: a tuple of two strings identifying the (Horz,Vert) anchor of the label (e.g. ('right','top'))
    :param color: the color of the label
    :return: Void
    """
    for val in LINES:
        if val==LINES[0] or val==LINES[-1]:
            unit = unitlabel
        else:
            unit = ''
        lbl = LABELS[val]
        dydx = lbl['dydx']
        ang = np.arctan(dydx*scalingratio) #convert the numeric slope to pixel coords
        slope = np.degrees(ang)
        label = numformat%val+unit
        axis.text(lbl['x'], lbl['y'], label,
                color=color,
                ha=location[0],
                va=location[1],
                #backgroundcolor='w',
                rotation=slope)

def Tp(mpobj, fig=None, ax=None, Tlim=None, plim=None, dlines=None):
    """Temperature-pressure diagram
"""

    # Select a figure
    if fig is None:
        if ax is not None:
            fig = ax.get_figure()
        else:
            fig = plt.figure()
    elif isinstance(fig, matplotlib.figure.Figure):
        pass
    else:
        fig = plt.figure(fig)
    
    # Select an axes
    if ax is None:
        fig.clf()
        ax = fig.add_subplot(111)
    
    if Tlim is None:
        Tlim = mpobj.Tlim()
        
    if plim is None:
        plim = mpobj.plim()
    
    Tc,pc,dc = mpobj.critical(density=True)
    Tt,pt = mpobj.triple()
    
    plim[0] = max(plim[0], pt)
    
    if dlines is None:
        dlim = [dc / 1000., dc]
        DLINES = np.flip(_log_interval(dlim[0], dlim[1], 10), 0)
    else:
        DLINES = np.asarray(dlines)
    
    Tn = (Tc - Tt) / 1000.

    # Generate lines
    T = np.linspace(Tlim[0]+Tn, Tlim[1]-Tn, 151)
    
    # Lines of constant density
    for d in DLINES:
        p = mpobj.p(T=T,d=d)
        ax.loglog(p,T,
                config['d_style'],
                color=config['d_color'],
                lw=config['d_width'])
                
    # Generate the dome
    T = np.linspace(Tt+Tn,Tc-Tn,101)
    p = mpobj.ps(T)

    ax.loglog(p,T,
            ls=config['sat_style'],
            color=config['sat_color'],
            lw=config['sat_width'])
        
    # Label the s-axis
    ax.set_xlabel('p [%s]'%(pm.config['unit_pressure']))
            
    # Label the T-axis
    ax.set_ylabel('T [%s]'%(
            pm.config['unit_temperature']))
        
    # Label the figure
    ax.set_title('%s T-p Diagram'%(mpobj.data['id']))
        
    plt.show(block=False)
    return ax


def Ts(mpobj, fig=None, ax=None, satlines=True, Tlim=None, vlines=None, plines=None, hlines=None, size=config['size'], display = True):
    """Temperature-enthalpy diagram
    ax = TS(mpobj)
    
"""
    # Select a figure
    if fig is None:
        if ax is not None:
            fig = ax.get_figure()
        else:
            fig = plt.figure(figsize=size)
    elif isinstance(fig, matplotlib.figure.Figure):
        pass
    else:
        fig = plt.figure(fig)
    
    # Select an axes
    if ax is None:
        fig.clf()
        ax = fig.add_subplot(111)
    
    if Tlim is None:
        Tlim = mpobj.Tlim()

    Tc,pc,dc = mpobj.critical(density=True)
    Tt,pt = mpobj.triple()

    plim = mpobj.plim()
    plim[0] = max(pt, plim[0])

    if vlines is None:
        #DLINES = _dlines(mpobj)
        VLINES = _vlines(mpobj)
    else:
        VLINES = np.asarray(vlines)
    
    if plines is None:
        PLINES = _plines(mpobj)
    else:
        PLINES = np.asarray(plines)

    if hlines is None:
        HLINES = _hlines(mpobj)
    else:
        HLINES = np.asarray(hlines)

    Tn = (Tc - Tt) / 1000.

    # Generate lines
    T = np.linspace(Tlim[0]+Tn, Tlim[1]-Tn, 151)
    
    # Lines of constant pressure
    PLABELS = {}
    for p in PLINES:
        s = mpobj.s(T=T,p=p)
        ax.plot(s,T,
                config['p_style'],
                color=config['p_color'], 
                lw=config['p_width'])
        PLABELS[p] = _get_slope(s, T, 1, 0.1, 'linear')
    
    # Lines of constant density
    VLABELS = {}
    for v in VLINES:
        s = mpobj.s(T=T,d=1/v)
        ax.plot(s,T,
                config['d_style'],
                color=config['d_color'],
                lw=config['d_width'])
        VLABELS[v] = _get_slope(s, T, 0.7, 0.1, 'linear')


    # Lines of constant enthalpy
    HLABELS = {}
    for h in HLINES[:]: #Copy HLINES for the iteration, so that we can remove ones that fail
        try:
            psp = np.logspace(np.log10(1e-5*plim[1]),np.log10(0.95*plim[1]),20)
            T, xh = mpobj.T_h(p=psp, h=h, quality=True)
            s = mpobj.s(T=T, p=psp)
            if (max(xh) > 0):
                s[xh > 0] = mpobj.s(T=T[xh > 0], x=xh[xh > 0])
            ax.plot(s, T,
                    config['h_style'],
                    color=config['h_color'],
                    lw=config['h_width'])
            HLABELS[h] = _get_slope(s, T, 0, 0.05, 'linear')
        except pm.utility.PMAnalysisError:
            HLINES.remove(h)
            print('h=',h,' failed due to iter1_() guess error')

    # Generate the dome
    T = np.linspace(Tt+Tn,Tc-Tn,101)
    ssL,ssV = mpobj.ss(T)

    ax.plot(ssL,T,
            ls=config['sat_style'],
            color=config['sat_color'],
            lw=config['sat_width'])
    ax.plot(ssV,T,
            ls=config['sat_style'],
            color=config['sat_color'],
            lw=config['sat_width'])

    # Get the scaling ratio for slopes
    r = _slope_ratio(ax)

    # LABELS of constant pressure
    units = '%s' % (pm.config['unit_pressure'])
    loc = ('right', 'top')
    color = config['p_color']
    numformat = '%.3g '
    _labellines(ax, PLINES, PLABELS, r, units, numformat, loc, color)

    # LABELS of constant volume
    units = '%s/%s' % (pm.config['unit_volume'], pm.config['unit_matter'])
    loc = ('right', 'top')
    color = config['d_color']
    numformat = '%0.3g '
    _labellines(ax, VLINES, VLABELS, r, units, numformat, loc, color)
        
    # LABELS of constant enthalpy
    units = '%s/%s' % (pm.config['unit_energy'], pm.config['unit_matter'])
    loc = ('left', 'top')
    color = config['h_color']
    numformat = '%0.d '
    _labellines(ax, HLINES, HLABELS, r, units, numformat, loc, color)

    # Label the s-axis
    ax.set_xlabel('s [%s/(%s%s)]'%(
            pm.config['unit_energy'],
            pm.config['unit_matter'],
            pm.config['unit_temperature']))
            
    # Label the T-axis
    ax.set_ylabel('T [%s]'%(
            pm.config['unit_temperature']))
        
    # Label the figure
    ax.set_title('%s T-S Diagram'%(mpobj.data['id']))

    if display:
        plt.show(block=False)
    return ax


def Tv(mpobj, fig=None, ax=None, satlines=True, Tlim=None, slines=None, plines=None, hlines=None, size=config['size'], display=True):
    """Temperature-volume diagram
    ax = Tv(mpobj)

"""
    # Select a figure
    if fig is None:
        if ax is not None:
            fig = ax.get_figure()
        else:
            fig = plt.figure(figsize=size)
    elif isinstance(fig, matplotlib.figure.Figure):
        pass
    else:
        fig = plt.figure(fig)

    # Select an axes
    if ax is None:
        fig.clf()
        ax = fig.add_subplot(111)

    #Critical and Tripe point properties
    Tc, pc, dc = mpobj.critical(density=True)
    Tt, pt = mpobj.triple()

    #auto compute T limits
    if Tlim is None:
        Tlim = mpobj.Tlim()

    #Compute pressure limits
    plim = mpobj.plim()
    plim[0] = max(pt, plim[0])

    #Get lines of Entropy, pressure and enthalpy
    if slines is None:
        SLINES = _slines(mpobj)
    else:
        SLINES = np.asarray(slines)

    if plines is None:
        PLINES = _plines(mpobj)
    else:
        PLINES = np.asarray(plines)

    if hlines is None:
        HLINES = _hlines(mpobj,n=5)
    else:
        HLINES = np.asarray(hlines)

    # Generate lines
    Tn = (Tc - Tt) / 1000.
    T = np.linspace(Tlim[0] + Tn, Tlim[1] - Tn, 151) #a base temperature vector

    # Lines of constant pressure
    PLABELS = {}
    for p in PLINES:
        d = mpobj.d(T=T, p=p)
        ax.semilogx(1/d, T,
                config['p_style'],
                color=config['p_color'],
                lw=config['p_width'])
        PLABELS[p] = _get_slope(1/d, T, 1, 0.1, 'logx')

    # Lines of constant entropy
    SLABELS = {}
    for s in np.copy(SLINES):
        try:
            psp = np.logspace(np.log10(1e-5 * plim[1]), np.log10(0.95 * plim[1]), 20)
            T, xh = mpobj.T_s(p=psp, s=s, quality=True)
            v = 1 / mpobj.d(T=T, p=psp)
            if (max(xh) > 0):
                v[xh > 0] = 1 / mpobj.d(T=T[xh > 0], x=xh[xh > 0])
            ax.plot(v, T,
                    config['d_style'],
                    color=config['d_color'],
                    lw=config['d_width'])
            SLABELS[s] = _get_slope(v, T, 0, 0.1, 'logx')
        except pm.utility.PMAnalysisError:
            try:
                p_s = pmsolve.solve1n('p', f=mpobj.T_s, param_init=1.5*plim[0])
                pmax = p_s(0.95*Tlim[1],s=s)
                psp2 = np.logspace(np.log10(1e-5 * plim[1]), np.log10(pmax), 20)
                T, xh = mpobj.T_s(p=psp2, s=s, quality=True)
                v = 1 / mpobj.d(T=T, p=psp2)
                if (max(xh) > 0):
                    v[xh > 0] = 1 / mpobj.d(T=T[xh > 0], x=xh[xh > 0])
                ax.plot(v, T,
                        config['s_style'],
                        color=config['s_color'],
                        lw=config['s_width'])
                SLABELS[s] = _get_slope(v, T, 0.75, 0.1, 'logx')
            except pm.utility.PMAnalysisError as E:
                SLINES = np.setdiff1d(SLINES,s) #removes s
                print('s=', s, ' failed due to iter1_() guess error')

    # Lines of constant enthalpy
    HLABELS = {}
    for h in np.copy(HLINES):  # Copy HLINES for the iteration, so that we can remove ones that fail
        try:
            psp = np.logspace(np.log10(1e-5*plim[1]),np.log10(0.95*plim[1]),25)
            T, xh = mpobj.T_h(p=psp, h=h, quality=True)
            v = 1/mpobj.d(T=T, p=psp)
            if (max(xh) > 0):
                v[xh > 0] = 1/mpobj.d(T=T[xh > 0], x=xh[xh > 0])
            ax.plot(v, T,
                    config['h_style'],
                    color=config['h_color'],
                    lw=config['h_width'])
            HLABELS[h] = _get_slope(v, T, 1, 0.05, 'logx')
        except pm.utility.PMAnalysisError:
            HLINES = np.setdiff1d(HLINES,h) #removes h
            print('h=',h,' failed due to iter1_() guess error')

    # Generate the dome
    T = np.linspace(Tt + Tn, Tc - Tn, 101)
    dsL, dsV = mpobj.ds(T)

    ax.semilogx(1/dsL, T,
            ls=config['sat_style'],
            color=config['sat_color'],
            lw=config['sat_width'])
    ax.semilogx(1/dsV, T,
            ls=config['sat_style'],
            color=config['sat_color'],
            lw=config['sat_width'])

    # Get the scaling ratio for slopes
    r = _slope_ratio(ax, scaling='logx')

    # LABELS of constant pressure
    units = '%s' % (pm.config['unit_pressure'])
    loc = ('right','top')
    color = config['p_color']
    numformat = '%.3g'
    _labellines(ax,PLINES,PLABELS,r,units,numformat,loc,color)

    # LABELS of constant enthalpy
    units = '%s/%s' % (pm.config['unit_energy'], pm.config['unit_matter'])
    loc = ('right','top')
    color = config['h_color']
    numformat = '%d '
    _labellines(ax,HLINES,HLABELS,r,units,numformat,loc,color)

    # LABELS of constant entropy
    units = '%s/(%s%s)' % (pm.config['unit_energy'], pm.config['unit_matter'],pm.config['unit_temperature'])
    loc = ('left','top')
    color = config['s_color']
    numformat = '%0.2g'
    _labellines(ax,SLINES,SLABELS,r,units,numformat,loc,color)

    # Label the v-axis
    ax.set_xlabel('v [%s/%s]' % (
        pm.config['unit_volume'],
        pm.config['unit_matter'],
        ))

    # Label the T-axis
    ax.set_ylabel('T [%s]' % (
        pm.config['unit_temperature']))

    # Label the figure
    ax.set_title('%s T-v Diagram' % (mpobj.data['id']))

    if display:
        plt.show(block=False)
    return ax

def pv(mpobj, fig=None, ax=None, satlines=True, plim=None, slines=None, Tlines=None, hlines=None, size=config['size'],display=True):
    """Pressure volume diagram
    ax = pv(mpobj)

"""
    # Select a figure
    if fig is None:
        if ax is not None:
            fig = ax.get_figure()
        else:
            fig = plt.figure(figsize=size)
    elif isinstance(fig, matplotlib.figure.Figure):
        pass
    else:
        fig = plt.figure(fig)

    # Select an axes
    if ax is None:
        fig.clf()
        ax = fig.add_subplot(111)

    Tc, pc, dc = mpobj.critical(density=True)
    Tt, pt = mpobj.triple()

    Tlim = mpobj.Tlim()
    #Tlim[1] = 1.1 * Tc

    if plim is None:
        plim = mpobj.plim()
        plim[0] = max(pt, plim[0])
        plim[0] = pc/20
        plim[1] = 3*pc

    if slines is None:
        SLINES = _slines(mpobj)
    else:
        SLINES = np.asarray(slines)

    if Tlines is None:
        TLINES = _Tlines(mpobj)
    else:
        TLINES = np.asarray(Tlines)

    if hlines is None:
        HLINES = _hlines(mpobj,n=10)
    else:
        HLINES = np.asarray(hlines)

    pn = (pc - pt) / 1000.

    # Generate lines
    p = np.linspace(plim[0]+pn, plim[1]-pn, 151)

    # Lines of constant temperature
    TLABELS = {}
    for T in TLINES:
        d = mpobj.d(T=T, p=p)
        ax.loglog(1/d, p,
                config['p_style'],
                color=config['p_color'],
                lw=config['p_width'])
        TLABELS[T] = _get_slope(1/d, p, 1, 0.1, 'loglog')

    # Lines of constant entropy
    SLABELS = {}
    for s in np.copy(SLINES):
        try:
            T, xh = mpobj.T_s(p=p, s=s, quality=True)
            v = 1 / mpobj.d(T=T, p=p)
            if (max(xh) > 0):
                v[xh > 0] = 1 / mpobj.d(T=T[xh > 0], x=xh[xh > 0])
            ax.plot(v, p,
                    config['d_style'],
                    color=config['d_color'],
                    lw=config['d_width'])
            SLABELS[s] = _get_slope(v, p, 0.01, 0.1, 'loglog')
        except pm.utility.PMAnalysisError:
            SLINES = np.setdiff1d(SLINES, s)  # removes s
            print('s=', s, ' failed due to iter1_() guess error')


    # Lines of constant enthalpy
    HLABELS = {}
    for h in np.copy(HLINES):  # Copy HLINES for the iteration, so that we can remove ones that fail
        try:
            #psp = np.logspace(np.log10(1e-5*plim[1]),np.log10(0.95*plim[1]),20)
            T, xh = mpobj.T_h(p=p, h=h, quality=True)
            v = 1/mpobj.d(T=T, p=p)
            if (max(xh) > 0):
                v[xh > 0] = 1/mpobj.d(T=T[xh > 0], x=xh[xh > 0])
            ax.plot(v, p,
                    config['h_style'],
                    color=config['h_color'],
                    lw=config['h_width'])
            HLABELS[h] = _get_slope(v, p, 0, .005, 'loglog')
        except pm.utility.PMAnalysisError:
            HLINES = np.setdiff1d(HLINES,h) #removes h
            print('h=',h,' failed due to iter1_() guess error')

    # Generate the dome
    pn = (pc - pt) / 1000.
    p = np.linspace(plim[0]+pn, pc-pn, 101)
    dsL, dsV = mpobj.ds(p=p)

    ax.loglog(1/dsL, p,
            ls=config['sat_style'],
            color=config['sat_color'],
            lw=config['sat_width'])
    ax.loglog(1/dsV, p,
            ls=config['sat_style'],
            color=config['sat_color'],
            lw=config['sat_width'])

    # Get the scaling ratio for slopes
    r = _slope_ratio(ax, scaling='loglog')

    # LABELS of constant temperature
    units = '%s' % (pm.config['unit_temperature'])
    loc = ('right','bottom')
    color = config['p_color']
    numformat = '%.4g '
    _labellines(ax,TLINES,TLABELS,r,units,numformat,loc,color)

    # LABELS of constant enthalpy
    units = '%s/%s' % (pm.config['unit_energy'], pm.config['unit_matter'])
    loc = ('left','top')
    color = config['h_color']
    numformat = '%d '
    _labellines(ax,HLINES,HLABELS,r,units,numformat,loc,color)

    # LABELS of constant entropy
    units = '%s/(%s%s)' % (pm.config['unit_energy'], pm.config['unit_matter'],pm.config['unit_temperature'])
    loc = ('center','bottom')
    color = config['s_color']
    numformat = '%0.2g'
    _labellines(ax,SLINES,SLABELS,r,units,numformat,loc,color)

    # Label the v-axis
    ax.set_xlabel('v [%s/%s]' % (
        pm.config['unit_volume'],
        pm.config['unit_matter'],
        ))

    # Label the p-axis
    ax.set_ylabel('p [%s]' % (
        pm.config['unit_pressure']))

    # Label the figure
    ax.set_title('%s p-v Diagram' % (mpobj.data['id']))

    if display:
        plt.show(block=False)
    return ax