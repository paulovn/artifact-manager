"""
Test the Artifact management when there are repeated artifacts
(i.e. same file in two places in the local dir)
"""

import datetime

import unittest
import pprint

from testaux import REPO_NAME, BRANCH_NAME
from testaux.am import am_mod, am_args_defaults
from testaux.server import TmpServer
from testaux.project import TmpProject


# --------------------------------------------------------------------

class TestRepeatedArtifact( unittest.TestCase ):

    def setUp(self):
        # Create an artifact server and a project to upload
        self.server = TmpServer( REPO_NAME )
        self.project = TmpProject( repeat=2 )
        # Create the repo & upload the project artifacts
        self.args = am_args_defaults( self.server, self.project )
        self.mgr = am_mod.ArtifactManager( self.args )

    def tearDown(self):
        self.server.delete()
        self.project.delete()


    def test01_upload(self):
        """Upload artifacts"""
        r = self.mgr.upload_artifacts( self.args.project_dir, BRANCH_NAME )
        self.assertEquals( 2, r, "uploaded files" )


    def test02_diff(self):
        """Test diff before & after uploading"""
        # Test before uploading
        l = self.mgr.local_print_changes( self.args.project_dir,
                                          BRANCH_NAME, False )
        self.assertEquals( 3, len(l['only in local']), "detected changes" )
        # Upload
        r = self.mgr.upload_artifacts( self.args.project_dir, BRANCH_NAME )
        self.assertEquals( 2, r, "uploaded" )
        # Test after uploading
        l = self.mgr.local_print_changes( self.args.project_dir,
                                          BRANCH_NAME, False )
        self.assertEquals( 0, len(l['only in local']), "no changes after upload" )

    def test02_move(self):
        """Test diff when moving an artifact"""
        # Upload
        r = self.mgr.upload_artifacts( self.args.project_dir, BRANCH_NAME )

        # Move a file
        self.project.moveArtifact()
        # Recreate the object (since the artifact list is cached)
        self.mgr = am_mod.ArtifactManager( self.args )

        # Check. We'll have 1 missing, 1 new
        l = self.mgr.local_print_changes( self.args.project_dir,
                                          BRANCH_NAME, False )
        self.assertEquals( 1, len(l['only in local']), "detected changes" )
        self.assertEquals( 1, len(l['only in server']), "detected changes" )

        # Upload again, overwriting the branch
        r = self.mgr.upload_artifacts( self.args.project_dir, BRANCH_NAME, True )

        # Check. No differences
        l = self.mgr.local_print_changes( self.args.project_dir,
                                          BRANCH_NAME, False )
        self.assertEquals( 0, len(l['only in local']), "no changes" )
        self.assertEquals( 0, len(l['only in server']), "no changes" )

        
        



# --------------------------------------------------------------------

if __name__ == '__main__':
    unittest.main()
