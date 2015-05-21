"""
Test the Artifact management with more than one backend branch
"""

import datetime

import unittest
import pprint

from testaux import REPO_NAME, BRANCH_NAME
from testaux.am import am_mod, am_args_defaults
from testaux.server import TmpServer
from testaux.project import TmpProject


# --------------------------------------------------------------------

class TestBranches( unittest.TestCase ):

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
        """Upload artifacts to 2 branches"""
        r = self.mgr.upload_artifacts( self.args.project_dir, BRANCH_NAME )
        self.assertEquals( 2, r, "uploaded 1" )
        r = self.mgr.upload_artifacts( self.args.project_dir, BRANCH_NAME+'2' )
        self.assertEquals( 0, r, "uploaded 2nd - 0 artifacts" )
        l = self.mgr.list_branches( self.args.project_dir )
        #self.assertEquals( 2, len(l), "num branches" )
        #self.assertEquals( set([BRANCH_NAME,BRANCH_NAME+'2']), set(l), "branches" )


    def test02_diff(self):
        """Diff two identical branches"""
        r = self.mgr.upload_artifacts( self.args.project_dir, BRANCH_NAME )
        self.assertEquals( 2, r, "uploaded 1" )
        r = self.mgr.upload_artifacts( self.args.project_dir, BRANCH_NAME+'2' )
        self.assertEquals( 0, r, "uploaded 2nd - 0 artifacts" )
        l = self.mgr.diff( BRANCH_NAME, BRANCH_NAME+'2', False )
        for t in l.itervalues():
            self.assertEquals( 0, len(t), "no diffs" )



    def test03_move(self):
        """Test diff with different branches"""
        # Upload
        r = self.mgr.upload_artifacts( self.args.project_dir, BRANCH_NAME )

        # Move a file
        self.project.moveArtifact()
        # Reset the local list, so that the new artifact is noticed
        self.mgr._reset_lists()

        # Upload again, to a 2nd branch
        r = self.mgr.upload_artifacts( self.args.project_dir, BRANCH_NAME+'2' )

        # Check. We'll have 1 only in one branch, one only in the other
        l = self.mgr.diff( BRANCH_NAME, BRANCH_NAME+'2', False )
        for t in l.itervalues():
            self.assertEquals( 1, len(t), "diffs" )
        



# --------------------------------------------------------------------

if __name__ == '__main__':
    unittest.main()
