import os
import shutil
import tempfile


# -------------------------------------------------------------------

def createTmpServer( repo=None ):
    """Create an artifact server (as a local folder)"""
    tmpbase = tempfile.mkdtemp()
    if repo is not None:
        os.mkdir( os.path.join(tmpbase,repo) )
    return tmpbase


def deleteTmpServer( name ):
    """Remove the artifact server"""
    shutil.rmtree( name )

