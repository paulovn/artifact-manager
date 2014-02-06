import imp
from testaux import REPO_NAME

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

def am_args_defaults( server, project ):
    """
    Create an object containing the options that the ArtifactManager class
    requires, using some defaults taken from a created temporal server
    & project
    """
    try:
        from __main__ import testrunner
        verbosity = testrunner.verbosity - 1
    except ImportError:
        verbosity = 0
    return am_args( { 'server_url': server.dir,
                      'verbose' : verbosity,
                      'repo_name' : server.repo if server.repo is not None else REPO_NAME,
                      'project_dir' : project.dir } )
