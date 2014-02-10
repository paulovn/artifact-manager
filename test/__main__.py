# --------------------------------------------------------------------------
# $Id: __main__.py 10779 2013-07-04 11:44:55Z mmartin $
# --------------------------------------------------------------------------
"""
A script to enable execution of any python unit test in this directory.
It will be called when Python tries to 'execute' this directory

**Usage:**

  * list all unit tests in this dir
       python <dir> [-q] -l        

  * execute all unit tests in this dir
       python <dir>        
       python <dir> [--all] [--exclude <test1,test2,...>] ...
       

  * execute a certain set of tests
       python <dir> [-v] <name1> <name2> ... 
"""

# Uncomment for remotely debug unit tests only
#import pydevd
#pydevd.settrace('10.95.61.185', port=5544, stdoutToServer=True, stderrToServer=True)


import unittest
import os.path
import sys
import re

from testaux.dirlist import all_scripts

# -------------------------------------------------------------------

# Default options
opt = type( "options", (), 
            { 'all' : False,
              'quiet' : False,
              'list' : False,
              'exclude': None,
              'verbosity': 1 } )
        

# Detect '-l', '-v', '-q', '-a' options
while len(sys.argv) > 1 and sys.argv[1].startswith('-'): 
    if sys.argv[1] == '-h':
        print "  Execute unit tests"
        print "  Usage: python test [-l] [-q | -v | -vv] [-a] [-e <name>] [name] .."
        sys.exit(1)
    elif sys.argv[1] == '-l':
        opt.list = True
    elif sys.argv[1] == '-q':
        opt.quiet = True
    elif sys.argv[1] == '-v':
        opt.verbosity = 2
    elif sys.argv[1] == '-vv':
        opt.verbosity = 3
    elif sys.argv[1] in ('-a','-all'):
        opt.all = True
    elif sys.argv[1] in ('-e','--exclude') and len(sys.argv) > 2:
        opt.exclude = sys.argv[2].split(',')
        sys.argv.pop(1)
    else:
        print "Warning: unknown option", sys.argv[1]
    sys.argv.pop(1)    # remove the just-used argument


# Select the test(s) to run
if __name__ != '__main__' or len(sys.argv) < 2 or opt.all:
    test_list = all_scripts( __file__ )
else:
    test_list = sys.argv[1:]

if opt.exclude:
    for e in opt.exclude:
        try:
            test_list.remove( e )
        except ValueError:
            print >>sys.stderr,"Warning: %s not in test list" % e

# List available tests (& exit)
if opt.list:
    if not opt.quiet:
        print " Available unit tests: ", 
        print [ s for s in test_list ]
    else:
        print ' '.join( test_list )
    sys.exit( 0 )


# Don't remove script name (some unit tests may need a non-empty sys.argv)
#sys.argv.pop(0)     # take out the name of *this* script


loader = unittest.defaultTestLoader
suite = unittest.TestSuite()


if not opt.quiet:
    print "\n******************************\n"

# Add all requested unit tests
for test in test_list:
    if not opt.quiet:
        print "Loading unit test '" + test + "'"
    suite.addTest( loader.loadTestsFromName( test ) )


# Run the tests
if not opt.quiet:
    print "\n\nRunning test suite\n"
try:
    testrunner = unittest.TextTestRunner( verbosity=opt.verbosity )
    testrunner.run( suite )
except KeyboardInterrupt as err:
    print "Interrupted!! :", err
    sys.exit(1)
