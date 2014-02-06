"""
Create & manage a local project with some artifact files
"""

import os
import shutil
import tempfile
import zipfile


def _populate_project( projectdir, repeat=1 ):
    d1 = os.path.join(projectdir,'dir1')
    d2 = os.path.join(projectdir,'dir2')
    os.mkdir( d1 )
    os.mkdir( d2 )
    s = os.path.join(projectdir,'sourceA.txt')
    with open(s,'w') as f:
        f.write('A simple file')
    for i in range(0,repeat):
        with zipfile.ZipFile( os.path.join(d1,'artifactA%d.zip'%i), 'w' ) as z:
            z.write( s )
    s = os.path.join(projectdir,'sourceB.txt')
    with open(s,'w') as f:
        f.write('Another simple file')
    with zipfile.ZipFile( os.path.join(d1,'artifactB.zip'), 'w' ) as z:
        z.write( s )


# -------------------------------------------------------------------

class TmpProject( object ):

    def __init__( self, repeat=1 ):
        """
        Create a local project and populate it with a few artifacts
        """
        tmpbase = tempfile.mkdtemp()
        _populate_project( tmpbase, repeat )
        self.dir = tmpbase


    # -------------------------------------------------------------------

    def delete( self ):
        """
        Delete a local project
        """
        shutil.rmtree( self.dir )


    # -------------------------------------------------------------------

    def moveArtifact( self, artifact='artifactB.zip', change_name=False ):
        """
        Move one artifact in the local project to another directory.
        Optionally change also its name
        """
        if change_name:
            base, ext = os.path.splitext( artifact )
            outname = base + '-changed' + ext
        else:
            outname = artifact
        d1 = os.path.join(self.dir,'dir1')
        d2 = os.path.join(self.dir,'dir2')
        os.rename( os.path.join(d1,artifact), os.path.join(d2,outname) )

    # -------------------------------------------------------------------

    def deleteArtifact( self, artifact='artifactB.zip' ):
        """
        Delete one artifact in the local project
        """
        d1 = os.path.join(self.dir,'dir1')
        os.unlink( os.path.join(d1,artifact) )
