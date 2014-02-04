import imp

# -------------------------------------------------------------------

# Load the artifact-manager file as a python module
am_mod = imp.load_source( 'am', 'artifact-manager' )

# -------------------------------------------------------------------

def am_args( values=None ):
    """
    Create an object containing the options that the ArtifactManager class
    requires
    """
    defaults = { 'verbose' : 0,
                 'dry_run' : False,
                 'subdir' : None }
    if values is None:
        values = {}
    for n,v in defaults.iteritems():
        if n not in values:
            values[n] = v
    return type('args',(object,), values )

# -------------------------------------------------------------------
