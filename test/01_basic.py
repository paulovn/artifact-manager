
import datetime

import unittest
import pprint

from testaux import REPO_NAME, BRANCH_NAME
from testaux.am import am_mod, am_args_defaults
from testaux.server import TmpServer
from testaux.project import TmpProject


# --------------------------------------------------------------------

class TestBasic( unittest.TestCase ):

    def setUp(self):
        # Create an artifact server and a project to upload
        self.server = TmpServer( REPO_NAME )
        self.project = TmpProject()
        from __main__ import testrunner
        # Create the repo & upload the project artifacts
        self.args = am_args_defaults( self.server, self.project )
        self.mgr  = am_mod.ArtifactManager( self.args )

    def tearDown(self):
        self.server.delete()
        self.project.delete()


    def test01_upload(self):
        """Upload artifacts"""
        r = self.mgr.upload_artifacts( self.args.project_dir, BRANCH_NAME )
        self.assertEquals( 2, r, "uploaded" )


    def test02_repeated_upload(self):
        """Upload artifacts, twice"""
        r = self.mgr.upload_artifacts( self.args.project_dir, BRANCH_NAME )
        self.assertEquals( 2, r, "uploaded" )
        # Try to upload without overwrite
        r = self.mgr.upload_artifacts( self.args.project_dir, BRANCH_NAME )
        self.assertIs( False, r, "upload should fail" )
        # Now upload with overwrite
        r = self.mgr.upload_artifacts( self.args.project_dir, BRANCH_NAME, True )
        self.assertEquals( 0, r, "re-upload, no new" )   # no new artifacts


    def test10_download_nobranch(self):
        """Download artifacts - no branch"""
        r = self.mgr.download_artifacts( BRANCH_NAME, self.args.project_dir )
        self.assertIs( False, r, "downloaded non-existing branch" )


    def test11_download_nonew(self):
        """Download artifacts - no new files"""
        r = self.mgr.upload_artifacts( self.args.project_dir, BRANCH_NAME )
        r = self.mgr.download_artifacts( BRANCH_NAME, self.args.project_dir )
        self.assertEquals( r, 0, "no downloads" )


    def test12_download(self):
        """Download artifacts"""
        r = self.mgr.upload_artifacts( self.args.project_dir, BRANCH_NAME )
        self.project.deleteArtifact()
        self.mgr._reset_lists() # clean cache in the object
        r = self.mgr.download_artifacts( BRANCH_NAME, self.args.project_dir )
        self.assertEquals( r, 1, "download 1 file" )


    def test20_diff(self):
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


    def test21_diff_all(self):
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
