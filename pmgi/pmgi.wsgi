#!/usr/bin/python3

# Add the PYroMat gateway interface to the system path
import sys
sys.path.insert(0, '/var/www/pmgi')

# import the application - it must be loaded as "application"
from pmgi import app as application
