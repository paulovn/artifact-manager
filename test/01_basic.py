
import datetime

import unittest
import pprint

from testaux import REPO_NAME, BRANCH_NAME
from testaux.am import am_mod, am_args
from testaux.server import createTmpServer, deleteTmpServer
from testaux.project import TmpProject


# --------------------------------------------------------------------

class TestBasic( unittest.TestCase ):

    def setUp(self):
        # Create an artifact server and a project to upload
        self.base = createTmpServer( REPO_NAME )
        self.project = TmpProject()
        # Create the repo & upload the project artifacts
        self.args = am_args( { 'server_url': self.base,
                               'repo_name' : REPO_NAME,
                               'project_dir' : self.project.dir } )
        self.mgr = am_mod.ArtifactManager( self.args )

    def tearDown(self):
        deleteTmpServer( self.base )
        self.project.delete()


    def test01_upload(self):
        """Upload artifacts"""
        r = self.mgr.upload_artifacts( self.args.project_dir, BRANCH_NAME )
        self.assertTrue( r, "uploaded" )


    def test02_repeated_upload(self):
        """Upload artifacts"""
        r = self.mgr.upload_artifacts( self.args.project_dir, BRANCH_NAME )
        self.assertTrue( r, "uploaded" )
        # Try to upload without overwrite
        r = self.mgr.upload_artifacts( self.args.project_dir, BRANCH_NAME )
        self.assertFalse( r, "not uploaded" )
        # Now upload with overwrite
        r = self.mgr.upload_artifacts( self.args.project_dir, BRANCH_NAME, True )
        self.assertTrue( r, "re-uploaded" )


    def test10_diff(self):
        """Test diff before & after uploading"""
        # Test before uploading
        l = self.mgr.local_print_changes( self.args.project_dir,
                                          BRANCH_NAME, False )
        self.assertEquals( 2, len(l['only in local']),  "detected changes" )
        self.assertEquals( 0, len(l['only in server']), "detected changes" )
        # Upload
        r = self.mgr.upload_artifacts( self.args.project_dir, BRANCH_NAME )
        self.assertTrue( r, "uploaded" )
        # Test after uploading
        l = self.mgr.local_print_changes( self.args.project_dir,
                                          BRANCH_NAME, False )
        self.assertEquals( 0, len(l['only in local']), "no changes")
        self.assertEquals( 0, len(l['only in server']), "no changes" )


    def test11_diff_all(self):
        """Test diff before & after uploading, show all files"""
        # Test before uploading
        l = self.mgr.local_print_changes( self.args.project_dir,
                                          BRANCH_NAME, True )
        self.assertEquals( 0, len(l['in both']),  "detected changes (B)" )
        self.assertEquals( 2, len(l['only in local']),  "detected changes (L)" )
        self.assertEquals( 0, len(l['only in server']), "detected changes (S)" )
        # Upload
        r = self.mgr.upload_artifacts( self.args.project_dir, BRANCH_NAME )
        self.assertTrue( r, "uploaded" )
        # Test after uploading
        l = self.mgr.local_print_changes( self.args.project_dir,
                                          BRANCH_NAME, True )
        self.assertEquals( 2, len(l['in both']),  "no changes (B)" )
        self.assertEquals( 0, len(l['only in local']), "no changes (L)")
        self.assertEquals( 0, len(l['only in server']), "no changes (S)" )
        



# --------------------------------------------------------------------

if __name__ == '__main__':
    unittest.main()
