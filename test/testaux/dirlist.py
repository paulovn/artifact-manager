import os
import re

# -------------------------------------------------------------------

def all_scripts( path ):
    """
    Get a list of all python scripts in a directory.

    function:: all_scripts( path )

    :param path Reference directory or file
    :rtype List of python scripts

    **Usage**
    If given a directory, it will return all scripts in that
    directory. If given a file, all scripts in the same directory.

    Scripts are taken as all files ending in ``.py`` that do not start
    with an underscore.
    """
    exp = re.compile( '^([^_\.].+)\.py$' )
    if os.path.isfile( path ):
        path = os.path.dirname( path )
    
    r = []
    for f in os.listdir(path):
        m = exp.match(f)
        if m:
            r.append( m.group(1) )
    return sorted(r)

