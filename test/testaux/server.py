"""
Create a local folder as a test artifact server
"""

import os
import shutil
import tempfile


# -------------------------------------------------------------------

class TmpServer( object ):

    def __init__( self, repo=None ):
        """Create an artifact server (as a local folder)"""
        tmpbase = tempfile.mkdtemp()
        if repo is not None:
            os.mkdir( os.path.join(tmpbase,repo) )
        self.dir = tmpbase
        self.repo = repo

    def delete( self ):
        """Remove the local folder for the artifact server"""
        shutil.rmtree( self.dir )

