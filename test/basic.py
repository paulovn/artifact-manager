# -------------------------------------------------------------------------
# $Id: filedb.py 8824 2012-09-04 10:43:27Z paulo $
# Test the itemdb & userdb classes, instantiated as filedb sources
# -------------------------------------------------------------------------

import datetime

import unittest
import pprint

from testaux.am import am_mod, am_args
from testaux.repo import createTmpServer, deleteTmpServer, createTmpProject, deleteTmpProject

REPO_NAME = 'test'
BRANCH_NAME = 'myBranch'

# --------------------------------------------------------------------

class TestBasic( unittest.TestCase ):

    def setUp(self):
        # Create an artifact server and a project to upload
        self.base = createTmpServer( REPO_NAME )
        self.project = createTmpProject()
        # Create the repo & upload the project artifacts
        self.args = am_args( { 'server_url': self.base,
                               'repo_name' : REPO_NAME,
                               'project_dir' : self.project } )
        self.mgr = am_mod.ArtifactManager( self.args )

    def tearDown(self):
        deleteTmpServer( self.base )
        deleteTmpProject( self.project )


    def test01_upload(self):
        """Upload artifacts"""
        r = self.mgr.upload_artifacts( self.args.project_dir, BRANCH_NAME )
        self.assertTrue( r, "uploaded" )

    def test02_diff(self):
        """Test diff before & after uploading"""
        # Test before uploading
        l = self.mgr.local_print_changes( self.args.project_dir,
                                          BRANCH_NAME, False )
        self.assertEquals( 1, len(l['only in local']), "changes" )
        # Upload
        r = self.mgr.upload_artifacts( self.args.project_dir, BRANCH_NAME )
        self.assertTrue( r, "uploaded" )
        # Test after uploading
        l = self.mgr.local_print_changes( self.args.project_dir,
                                          BRANCH_NAME, False )
        self.assertEquals( 0, len(l['only in local']), "changes" )
        



# --------------------------------------------------------------------

if __name__ == '__main__':
    unittest.main()
