# Tools for producing CGI content from PYroMat
# 

import os
import sys
import numpy as np
import cgi

config = {}
cgi_args = cgi.FieldStorage()


def error_response(message):
    print("Content-type: text/html")
    print("")
    print("<html>")
    print("<head></head><body>")
    print("<h1>Error</h1>")
    print(message)
    print("</body></html>")


def argparse(args):
    """Pull arguments from cgi form interface and convert them to requested type

    arg1, arg2, ... = argparse([('arg1', float), ('arg2', int, 3), ...])

The ARGS list names the arguments to find from the cgi form.  The 
simplest way to request an argument value is by simply specifying its
name as a string.  The values will be returned as strings.

    arg1, arg2 = argparse(['arg1', 'arg2'])

If the elements are tuples, then the first value is the argument name 
and the second is the type to which the value should be converted.  

    arg1, arg2 = argparse([('arg1', float), ('arg2', int)])

If there is a third element in the argument tuples, it is treated as a 
default value to be applied if the argument is not found.  Arguments 
with no default values that are omitted are treated as mandatory.

    arg1, ... = argparse([('arg1', float, 3.5), ... ])

These modes may be intermixed.  Each element of the argument list is
treated individually.

If a mandatory argument is not found or if type conversion fails, then 
the function will print an error page to stdout and evoke the exit() 
funciton.
"""
    out = []
    # Now a global variable
    #cgi_args = cgi.FieldStorage()
    for this in args:
        conv = str
        default = None
        if isinstance(this, tuple):
            arg = this[0]
            if len(this) > 1:
                conv = this[1]
            if len(this) > 2:
                default = this[2]
        else:
            arg = this
            
        if arg not in cgi_args:
            if default is None:
                error_response("The mandatory argument, " + arg + ", was not supplied.")
                exit()
            else:
               out.append(default)
        else:
            try:
                out.append(conv(cgi_args[arg].value))
            except:
                error_response("The " + arg + " value, " + repr(cgi_args[arg].value) + " failed to be converted by " + repr(conv) + ".")
                exit()
    return out
        

def buildget():
    """Build a GET arg string equivalent to the one supplied
"""
    out = '?'
    # Now a global variable
    #cgi_args = cgi.FieldStorage()
    kk = cgi_args.keys()
    while kk:
        this = kk.pop(0)
        out += this + '=' + str(cgi_args[this].value)
        if kk:
            out += '&'
    return out
    

def idgen(length=32, charset=None):
    """Generate a random series of characters
    id = idgen(length=32, charset=None)

A series of quasi-random ascii characters are returned in a string.  The
characters are selected from the CHARSET list or string of valid 
characters.  Unless CHARSET is defined, the alpha characters will be 
used.
"""
    if charset is None:
        charset = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
    return ''.join([
            charset[np.random.randint(0,len(charset))] 
            for index in range(length)
                ])
            

class PMPage:
    """This is a class for constructing a page in CGI
The PMPage class loads text from a template html file and exposes 
methods to edit it on the fly.  The intention is that a CGI script 
constructed in Python should use the PMPage class to load and modify a
template html file.

This example looks for a div element and replaces its contents with the
text "This is working!".

>>> P = PMPage('path/to/template.html')
>>> newtext = 'This is working!'
>>> P.replace(newtext, start='<div id="test">', stop='</div>')

Alternately, if the starting and ending tags are to also be replaced, 
set the optional KEEP keyword to False.

>>> P = PMPage('path/to/template.html')
>>> newtext = '<div id="test" class="pretty">This is working!</div>'
>>> P.replace(newtext, start='<div id="test">', stop='</div>', keep=False)

To simply explicitly replace a piece of text, leave the stop parameter
out.  In this case, the keep parameter is ignored, and the entire text
will always be replaced.

>>> P = PMPage('path/to/template.html')
>>> P.replace('<div id="test" class="pretty">', start='<div id="test">')

Once modifications are complete, write the output with the write() 
method.

>>> P.write()

For debugging, it may be useful to redirect the output away from stdout
to a file.

>>> P.write(dest='path/to/destination.html')
    OR
>>> with open('path/to/destination.html','w') as ff:
...     P.write(dest=ff)

"""
    def __init__(self, fromfile):
        self.fromfile = fromfile
        self._text = ''
        self._insert = []
        self.load()
        
    def load(self):
        """Load the template file into self._text
"""
        with open(self.fromfile, 'r') as ff:
            self._text = ff.read()


    def insert(self, text, start, stop=None, wait=False):
        """Insert text by line and column number
    Page.insert( text, (line, column))
        OR
    Page.insert( text, start=(line, column), stop=(line,column))
        OR
    Page.insert(text, start=(line, column), wait=True)
    
Faster than using fnr, INSERT uses the line number and column number 
from the original file to identify the start and stop for the insert.
If there is no stop, then text will be inserted at line, column without
replacing any text.  If a stop location is specified, then all the text
between start and stop will be replaced with the new text.

For example, consider a file with the text:
---
I do not smirk, but if I did, this 
would be a good opportunity.  Sir,
I protest.  I am not a merry man!
If winning is not important, then
Commander, why keep score?
---
The original file is 5 lines, and the longest has 35 characters 
(including a trailing space).  

To insert without deleting, one might call
>>> Page.insert( "Today \nis a good day to die.  ", (1, 30))

To replace the word "smirk" with "dance", one might call
>>> Page.insert( "dance", (0, 9), (0,14))

The total result of which would be
---
I do not dance, but if I did, this 
would be a good opportunity.  Today
is a good day to die.  Sir,
I protest.  I am not a merry man!
If winning is not important, then
Commander, why keep score?
---

*** WAIT ***
Because the order in which successive insertions are performed is 
essential, they should always be executed end-to-beginning.  To make 
matters worse, multiple insertions means multiple scannings of the 
entire document looking for newlines and counting columns.  For greater
efficiency, the insertion can be scheduled but not executed in the Page
object.  In this way, many insertions can be scheduled then executed all
at once.

>>> Page.insert(..., wait=True)
>>> Page.insert(..., wait=True)
>>> Page.insert(..., wait=True)
>>> Page.insert_exec()

Calling insert() without a wait=True directive will not only execute the
current insertion, but all other pending insertions as well.
"""
        # Verify the inputs
        if not isinstance(start,tuple):
            raise Exception('PMCGI: insert() start must be a tuple')
        elif len(start)!=2 or not isinstance(start[0],int) or not isinstance(start[1],int):
            raise Exception('PMCGI: insert() start must be a tuple of two integers.')
        

        if stop is None:
            # If there is no stop, then it is the start string.
            self._insert.append(start + start + (text,))
        else:
            # Verify the inputs
            if not isinstance(stop,tuple):
                raise Exception('PMCGI: insert() start must be a tuple')
            elif len(stop)!=2 or not isinstance(stop[0],int) or not isinstance(stop[1],int):
                raise Exception('PMCGI: insert() start must be a tuple of two integers.')

            self._insert.append(start + stop + (text,))
            
        if not wait:
            self.insert_exec()


    def insert_exec(self, nl='\n'):
        """See insert() documentation"""
        # Organize the insertions in order by insertion location
        self._insert.sort()
        # now, map out the lines
        newlines = []
        index = self._text.find(nl)
        while index>=0:
            newlines.append(index)
            index = self._text.find('\n',index+1)
        
        while self._insert:
            line, col, stopline, stopcol, text = self._insert.pop()
            ii = newlines[line-1] + col + 1 if line>0 else col
            jj = newlines[stopline-1] + stopcol + 1 if stopline>0 else stopcol
            self._text = self._text[:ii] + text + self._text[jj:]
        

    def find_line(self, text):
        """Return the line number where the first instance of "text" is found.
    line = Page.find_line(text)
    
This is useful in combination with insert() operations.  The intended 
use case is that comment tags "<!-- A -->" could be inserted in key 
locations so the line numbers used in the insert operations will be less
brittle to changes made in the file.  The entire line must be identical
to the text being tested.

For example, if a comment tag were
placed the line before an important segment:

line = Page.find_line("<!-- A -->")
Page.insert(new_text, (line+1, col))
"""
        start = 0
        stop = self._text.find('\n',start)
        line = 0
        while stop>=0 and start<len(self._text):
            if self._text[start:stop] == text:
                return line
            line +=1
            start=stop+1
            stop = self._text.find('\n',start)
        # If this is the last line
        if self._text[start:] == text:
            return line
        
        return -1
                
                

    def fnr(self, text, start, stop=None, incl=False):
        """Find-N-Replace text in the template file text
    Page.fnr( replace_with, start )
        OR
    Page.fnr( replace_with, start, stop )
        OR
    Page.fnr( replace_with, start, stop, keep=False)
    
The REPLACE method searches the page for a block of text and replaces it
with the text in REPLACE_WITH.  There are three modes:
1) Explicit replace:
    When only the START string is given, REPLACE searches for the first
    instance of START in the file text and replaces it.  The KEEP 
    parameter is ignored.
2) Bounded replace:
    When the START and STOP strings are both supplied, REPLACE 
    searches for the first instance of START in the text body, then 
    looks for the first instance of the STOP string in the text body.  
    The text between them is then replaced.
3) Inclusive bounded replace:
    When the START and STOP strings are both supplied and the INCL
    keyword is set to True, REPLACE will perform a bounded replace, but
    the START and STOP strings will be included in the text to be 
    replaced.
"""
    
        index0 = self._text.find(start)
        if index0<0:
            raise Exception('PMPage REPLACE: Failed to find start text "%s"'%start)
        index0 += len(start)
        
        if stop:
            index1 = self._text[index0:].find(stop)
            if index1<0:
                raise Exception('PMPage REPLACE: Failed to find stop text "%s"'%stop)
            index1 += index0
            if incl:
                index1 += len(stop)
                index0 -= len(start)
        else:
            index1 = index0
            index0 -= len(start)
        
        self._text = self._text[:index0] + text + self._text[index1:]


    def write(self, dest=sys.stdout):
        if hasattr(dest,'write'):
            dest.write(self._text)
        else:
            with open(dest,'w') as ff:
                ff.write(self._text)
            

def pageA(title,segment):
    with open('test.html','w') as ff:
        ff.write(\
"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>""" + title + """</title>
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
td.tdC {
    text-align: center;
    padding: 2px 15px 2px 15px;
}
td.tdR {
    text-align: right;
    padding: 2px 15px 2px 15px;
}
td.tdL {
    text-align: left;
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
#sec1 {
    width: 800px;
    font-size: 12pt;
    text-align: left;
}
#sec2 {
    width: 800px;
}
#sec3 {
    width: 
}

</style>
</head>
<body>""" + segment + '</body></html>')



def html_select(values, labels=None, sname=None, sid=None, sclass=None,\
        selected=None, select=True):
    """HTML_SELECT - construct an html select (dropdown menu)
    html_text = html_select(values)
    
This function constructs the markup language for representing a dropdown
menu in html.  The VALUES list is interpreted as a list of choices to
include in the menu.  The SNAME, SID, and SCLASS keywords specify the
name, id, and class assigned to the select.  For example,

>>> html_select(['a','b'], name='letter')

produces markup
<select name="letter"><option value="a">a</option><option value="b">b</option></select>

If the SELECT keyword is set to False, then the bracketing <select>
</select> elements will be omitted.  This is useful for inserting 
<option></option> elements in an existing select.

Notice that by default the text displayed for each option will be the 
same as the value.  To change this behavior, set the keyword, LABELS, to 
a second list of strings with the corresponding strings to be displayed.
For example

>>> html_select(['a','b'], text=['A','B'], select=False)

produces markup
<option value="a">A</option><option value="b">B</option>

The SELECTED keyword allows an option to be selected by default.  The
specified value should correspond to the option's value and not its 
text.
>>> html_select(['a','b'], text=['A','B'], select=False, selected='a')

produces markup
<option value="a" selected>A</option><option value="b">B</option>
"""
    out = ""
    # Create the starting select
    if select:
        out += '<select'
        if sname:
            out += ' ' + name
        if sid:
            out += ' ' + sid
        if sclass:
            out += ' ' + sclass
    # Build the menu
    for index,value in enumerate(values):
        # If the labels are not specified, use the values
        label = value if labels is None else labels[index]
        out += '<option value="' + value + '"'
        if value == selected:
            out += " selected"
            selected = None
        out += '>' + label + '</option>'
    return out


def html_column_table(labels, units, columns, 
        align='d', scale='m', sf=6, largep=3, smallp=-3, 
        radix='.', thousands=' ', thousandths=' '):
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
    
thousands, thousdandths
    The THOUSANDS and THOUSANDTHS keywords indicate which character 
    should be used for separating long numbers into groups of thousands.
    Common choices are ' ' (space) ',' (comma) or '.' (period).  
    THOUSANDS is applied left of the radix and THOUSANDTHS is applied to
    the right.
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
    ID = idgen()

    # pre-process the columns
    for ii in range(Ncol):
        C = columns[ii]
        try:
            pp = int(np.floor(np.log10(np.max(np.abs(C)))))
        except OverflowError: #Occurs, e.g. when quality is zero, resulting in infinite log10
            pp = 0 #just call it O(1)
        except TypeError: #can't convert, is it a string?
            pp = 0
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
    
    # Start building the table
    out = '<table class="ptab" id="' + ID + '">\n'
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
            # Grab the value to be converted to text
            try:
                this = float(columns[jj][ii])
            except ValueError: #Assume it's a string?
                this = str(columns[jj][ii])
                # Case out the column alignment modes
                if align[jj] == 'd':
                    out += '<td class=tdC>' + this + '</td><td></td>'
                elif align[jj] == 'l':
                    out += '<td class=tdL>' + this + '</td>'
                elif align[jj] == 'c':
                    out += '<td class=tdC>' + this + '</td>'
                elif align[jj] == 'r':
                    out += '<td class=tdR>' + this + '</td>'
                continue #move on
            
            # Extract the sign and detect the place of the most
            # significant digit
            if this<0:
                this=abs(this)
                pp = int(np.floor(np.log10(this)))
                sign = '-'
            elif this==0:
                sign = ''
                pp = 0
            else:
                pp = int(np.floor(np.log10(this)))
                sign = ''
            
            # Case out the scaling modes
            # In multiplier mode
            if scale[jj]=='m':
                # Apply the multiplier
                if M[jj]:
                    this *= 10**(-M[jj])
                    pp-=M[jj]
                pwr = ''
            # In engineering/scientific mode
            elif scale[jj] == 'e':
                # Round to the nearest thousands
                mm = (pp / TH) * TH
                if mm:
                    # Rescale the number
                    this /= 10**mm
                    pp -= mm
                    pwr = '&times10<sup>{:d}</sup>'.format(mm)
                else:
                    pwr = ''
            # If the scaling mode is None
            elif scale[jj] == 'n':
                pwr = ''
            else:
                return 'HTML_COLUMN_TABLE: Unrecognized scaling mode ' + scale[jj] + '\n'

            # Now that the number has been scaled, convert it to whole
            # and fractional parts
            if this==0:
                whol = '0'
                frac = ''
            else:
                # Build the whole and fractional strings in three cases:
                # There are more whole digits than sigfigs
                if pp > sf[jj]:
                    frac = ''
                    whol = '{:d}'.format( int(np.round(this,sf[jj]-pp)))
                # There are no whole digits
                elif pp<0:
                    whol = '0'
                    # Promote the significant figures to an integer
                    temp = int(np.round(this*10**(sf[jj]-pp-1)))
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
                    # Promote the significant figures to an integer
                    # How many fractional digits are left?
                    pp = sf[jj] - pp - 1
                    temp = int(np.round((this-temp)*10**pp))
                    if temp>0:
                        frac = ('{:0' + str(pp) + '}').format(temp)
                    else:
                        frac = ''

            # Deal with the thousands separator
            if thousands:
                temp = whol[-TH:]
                for kk in range(-TH, -len(whol), -TH):
                    temp = whol[kk-TH:kk] + thousands + temp
                whol = temp
            if thousandths:
                temp = ''
                for kk in range(0,len(frac),TH):
                    temp += frac[kk:kk+TH] + thousandths
                frac = temp
                
            # Case out the column alignment modes
            if align[jj] == 'd':
                out += '<td class=tdDL>' + sign + whol + radix + '</td><td class=tdDR>'\
                        + frac + pwr + '</td>'
            elif align[jj] == 'l':
                out += '<td class=tdL>' + sign + whol + radix + frac + pwr + '</td>'
            elif align[jj] == 'c':
                out += '<td class=tdC>' + sign + whol + radix + frac + pwr + '</td>'
            elif align[jj] == 'r':
                out += '<td class=tdR>' + sign + whol + radix + frac + pwr + '</td>'
                
        out += '</tr>'
        
    
    out += '</table>'
    return out
