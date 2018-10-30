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
td.tabhe {
    text-align: center;
    font-weight: bold;
}
</style>
</head>
<body>""" + segment + '</body></html>')


def html_sigfig(number, sf=6):
    """HTML_SIGFIG - represent a number with a finite significant digits
    text = html_sigfig(number, sf=6)
    
Returns a string representation of a number with SF significant figures
"""
    # How big is the number?
    pp = int(math.floor(math.log10(number)))
    

def html_sigdata(data, sf=6, ):
    """HTML_SIGDATA - generate a format string to be used on a data set
    fmt = html_sigdata(data, sf=6)

Data may be a multi-dimensional numpy array or nested lists.  The format
specifier will be selected so that SF significant figures are displayed.
The largest magnitude number determines how the data are to be 
displayed.  If the the magnitude is greater than the number of 
significant figures or is smaller than 1e-3, then the format defaults
"""
    # What is the most significant place?
    pp = int(np.floor(np.log10(np.abs(np.asarray(data)).max())))



def html_table(labels, *cols):
    """HTML_TABLE - construct an html table from 1D data
    html_text = cgi_table(labels=None, col1, col2, ...)
    
Constructs an html table from numeric data in colX with a header 
constructed from LABELS.  LABELS should be a list of strings with an 
entry corresponding to each of the columns.  If LABELS is a nested list,
it will be used to construct a multi-line header.  For example, the 
following might be used to construct a three-column table with a two-
line header establishing labels and units.

    cgi_table( [['Temperature', 'Pressure', 'Specific Heat'],\
                ['K', 'bar', 'kJ/kg/K']],\
                T, p, cp )
"""

    out = '<table>\n'
    start_header_row = '<tr>'
    stop_header_row = '</tr>\n'
    header_entry_fmt = '<td class="tabhe">{:s}</td>'

    start_row = '<tr>'
    stop_row = '</tr>'
    entry_fmt = '<td class="tabe">{:f}</td>'
    empty_fmt = '<td></td>'
    
    # Establish the table shape
    Ncol = len(cols)
    Nrow = 0
    for column in cols:
        Nrow = max(Nrow, len(column))
    
    if labels:
        # Enforce that labels is a list
        if not isinstance(labels, list):
            out = 'CGI_TABLE: LABELS was not a list.\n'
            sys.stderr.write(out)
            return out
        # Check for a nested list
        if not isinstance(labels[0], list):
            labels = [labels]
        # Generate the header
        for row in labels:
            out += start_header_row
            for entry in row:
                out += header_entry_fmt.format(entry)
            out += stop_header_row
        out += '<tr><td colspan={:d}> <hr /></td></tr>\n'.format(Ncol)
        
    # Generate the data
    for row in range(Nrow):
        out += start_row
        for column in cols:
            # 
    out += '</table>'
    return out
