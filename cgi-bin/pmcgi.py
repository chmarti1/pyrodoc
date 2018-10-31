# Tools for producing CGI content from PYroMat
# 

import os
import sys
import numpy as np

config = {}


def test(segment):
    with open('test.html','w') as ff:
        ff.write(\
"""<!DOCTYPE html>
<html>
<head>
<title>Test</title>
<style>
th {
    text-align: center;
    font-weight: bold;
    font-size: 12pt;
}
tr.trU {
    text-align: center;
    font-size: 10pt;
}
tr.trE {
    font-size: 10pt;
}
tr.tdC {
    text-align: center;
    padding: 2px 15px 2px 15px;
}
tr.tdR {
    text-align: center;
    padding: 2px 15px 2px 15px;
}
td.tdL {
    text-align: center;
    padding: 2px 15px 2px 15px;
}
td.tdDL {
    text-align: right;
    padding: 2px 0px 2px 15px;
}
td.tdDR {
    text-align: left;
    padding: 2px 15px 2px 0px;
}
</style>
</head>
<body>""" + segment + '</body></html>')



def html_column_table(labels, units, columns, 
        align='d', scale='m', sf=6, largep=3, smallp=-3, 
        radix='.', thousands=' '):
    """HTML_COLUMN_TABLE - construct an html table from 1D data
    html_text = html_column_table(labels, units, columns)

This funciton constructs the markup language for representing numerical
data in an HTML table.  The table is assumed to be constructed form a 
series of distinct columns; each of which has a label and a unit label.

labels, units
    These are lists containing string labels for each column.  The 
    LABELS list may be a nested list if multiple rows are needed to 
    represent the column labels.  Each element of the outer list is 
    interpreted as a row of labels.
    
    The UNITS are treated separately so the SCALE parameter can be 
    applied automatically.  (see below)

align
    The alignment mode determines how the data are aligned in their 
    columns.  The keyword accepts a single character to indicate the 
    mode:
    --->'d' (decimal)
    In this mode, the columns are aligned by the radix (decimal).  this
    is done by splitting each data column into two columns
    --->'l' (left), 'r' (right), 'c' center
    In these modes, the columns are aligned as specified.
    
    When ALIGN is given as a list of characters, they are interpreted as
    applying to each column individually.
    
scale
    The scaling mode indicates whether and how to re-scale the data 
    before displaying them.  Data sets with very large or very small 
    numbers are difficult to view, so they can be reconfigured.  The 
    scaling rule will be triggered when a data set's largest magnitude 
    number has a most significant digit left of the LARGEP place or 
    right of the SMALLP place.  
    
    When the SCALE parameter is given as a list of characters, they are 
    interpreted as applying to each column individually.
    
    The keyword accepts a single character to indicate the mode:
    --->'n' (no rescaling)
    The data will be displayed using a standard {:d} or {:f} specifier
    regardless of its size.
    --->'m' (multiplier)
    In multiplier mode, a multiplier to the nearest thousands will be
    applied to the entire column and noted in the units line.  If the 
    most significant digit of the largest magnitude number is left of 
    the LARGEP place or right of the SMALLP place, the multiplier will
    be applied.
    --->'e' (exponential)
    In exponential mode, columns with large or small numbers are
    displyed with scientific notation.
    
radix
    The RADIX (or decimal point) indicates the character to use for the
    radix.  By default, it is '.' but many countries use ','
    
thousands
    The THOUSANDS keyword indicates which character should be used for
    separating long numbers into groups of thousands.  Common choices
    are ' ' (space) ',' (comma) or '.' (period).
"""

    TH = 3  # Thousands break integer

    # First, process the options.
    # Detect the number of columns
    Ncol = len(columns)     # Number of data columns
    Ntcol = Ncol            # Number of table columns (we'll modify this later)
    Nrow = 0                # initialized (we'll modify this later)
    # If align is a string, broadcast it to all columns
    if isinstance(align, str):
        align = [align]*Ncol
    elif len(align)!= Ncol:
        return 'HTML_COLUMN_TABLE: the ALIGN list does not agree with the number of columns'
    # If scale is a string, broadcast it to all columns
    if isinstance(scale, str):
        scale = [scale]*Ncol
    elif len(scale)!= Ncol:
        return 'HTML_COLUMN_TABLE: the SCALE list does not agree with the number of columns'
    # If the significant figures is an integer, broadcast it to all columns
    if isinstance(sf, int):
        sf = [sf]*Ncol
    elif len(sf)!=Ncol:
        return 'HTML_COLUMN_TABLE: the SF list does not agree with the number of columns'

    # Enforce that labels is a list
    if not isinstance(labels, list):
        return 'HTML_COLUMN_TABLE: LABELS was not a list.'
    # Check for a nested list
    if labels and not isinstance(labels[0], list):
        labels = [labels]
    for row in labels:
        if len(row)!=Ncol:
            return 'HTML_COLUMN_TABLE: the LABELS list does not agree with the number of columns'

    # Enforce that units is a list
    if isinstance(units, list):
        for this in units:
            if not isinstance(this, str):
                return 'HTML_COLUMN_TABLE: UNITS must be a list of strings.'
    else:
        return 'HTML_COLUMN_TABLE: UNITS was not a list.'
    if units and len(units)!=Ncol:
        return 'HTML_COLUMN_TABLE: the UNITS list does not agree with the number of columns'
    
        


    # Initialize some metrics on the data
    P = [0] * Ncol     # P is the place of the most significant digit
    M = [0] * Ncol     # M is the column multiplier
    rescale_f = False
    
    # pre-process the columns
    for ii in range(Ncol):
        C = columns[ii]
        pp = int(np.floor(np.log10(np.max(np.abs(C)))))
        P[ii] = pp
        # If the multiplier is being used
        if scale[ii] == 'm':
            if pp<smallp:
                rescale_f = True
                M[ii] = TH*int(np.ceil(float(pp)/TH))
            elif pp>largep:
                rescale_f = True
                M[ii] = TH*int(np.floor(float(pp)/TH))
        # Detect the number of actual table columns
        if align[ii] == 'd':
            Ntcol += 1
        # Detect the number of rows
        Nrow = max(Nrow, len(C))
    
    print P, M
    
    # Start building the table
    out = '<table>\n'
    # Column labels
    if labels:
        # Generate the header
        for row in labels:
            out += '<tr>'
            for ii in range(Ncol):
                if align[ii] == 'd':
                    out += '<th colspan=2>' + row[ii] + '</th>'
                else:
                    out += '<th>' + row[ii] + '</th>'
            out += '</tr>\n'
    # Column units
    if units or rescale_f:
        out += '<tr class=trU>'
        for ii in range(Ncol):
            if align[ii]=='d':
                out += '<td colspan=2>'
            else:
                out += '<td>'
                
            if M[ii]:
                out += '(&times10<sup>{:d}</sup>) '.format(M[ii])
            if units:
                out += units[ii] + '</td>'
        out += '</tr>'
        
    # Horizontal rule
    out += '<tr><td colspan={:d}> <hr /></td></tr>\n'.format(Ntcol)
    
    # Construct the data one row at a time
    for ii in range(Nrow):
        out += '<tr class=trE>'
        for jj in range(Ncol):
            this = columns[jj][ii]
            # Case out the scaling modes
            # In multiplier mode
            if scale[jj]=='m':
                # Apply the multiplier
                if M[jj]:
                    this *= 10**(-M[jj])
                # Where is the most significant digit?
                if this:
                    pp = int(np.floor(np.log10(np.abs(this))))
                else:
                    pp = 0
                # Build the whole and fractional strings in three cases:
                # There are more whole digits than sigfigs
                if pp > sf[jj]:
                    frac = ''
                    whol = '{:d}'.format( int(np.round(this,sf[jj]-pp)))
                # There are no whole digits
                elif pp<0:
                    whol = '0'
                    # Promote the significant figures to an integer
                    temp = int(np.round(this*10**sf[jj]))
                    # If the result is significant
                    if temp:
                        frac = '0'*(-pp-1) + '{:d}'.format(temp)
                    else:
                        frac = '0'
                # If the number straddles the radix
                else:
                    # Isolate the whole part
                    temp = int(this)
                    whol = '{:d}'.format(temp)
                    # Isolate the fractional part
                    temp = abs(this - temp)
                    # Promote the significant figures to an integer
                    temp = int(np.round(temp*10**(sf[jj]-pp-1)))
                    frac = '{:d}'.format(temp)
                
            elif scale[jj]=='e':
                # Where is the most significant digit?
                pp = int(np.floor(np.log10(np.abs(this))))
                
            elif scale[jj] == 'n':
                pass
            
            # Case out the column alignment modes
            if align[jj] == 'd':
                out += '<td class=tdDL>' + whol + '</td><td class=tdDR>'\
                        + radix + frac + '</td>'
            elif align[jj] == 'l':
                out += '<td class=tdL>' + whol + radix + frac + '</td>'
            elif align[jj] == 'c':
                out += '<td class=tdC>' + whol + radix + frac + '</td>'
            elif align[jj] == 'r':
                out += '<td class=tdR>' + whol + radix + frac + '</td>'
                
        out += '</tr>'
        
    
    out += '</table>'
    return out
