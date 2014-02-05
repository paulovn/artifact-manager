
import datetime

import unittest
import pprint

from testaux import REPO_NAME, BRANCH_NAME
from testaux.am import am_mod, am_args
from testaux.server import createTmpServer, deleteTmpServer
from testaux.project import TmpProject


# --------------------------------------------------------------------

class TestLog( unittest.TestCase ):

    def setUp(self):
        # Create an artifact server and a project to upload
        self.base = createTmpServer( REPO_NAME )
        self.project = TmpProject()
        # Create the repo & upload the project artifacts
        self.args = am_args( { 'server_url': self.base,
                               'repo_name' : REPO_NAME,
                               'project_dir' : self.project.dir } )
        self.mgr = am_mod.ArtifactManager( self.args )
        self.mgr.upload_artifacts( self.args.project_dir, BRANCH_NAME )

    def tearDown(self):
        deleteTmpServer( self.base )
        self.project.delete()


    def test01_log(self):
        """Set a log message for the branch and get it back"""
        msg = self.mgr.get_log( BRANCH_NAME )
        self.assertEqual( '', msg, "empty log message" )
        self.mgr.put_log( BRANCH_NAME, 'This Is A Log' )
        msg = self.mgr.get_log( BRANCH_NAME )
        self.assertEqual( 'This Is A Log', msg, "log message set" )


    def test02_log_rename_branch(self):
        """Rename a branch and check that the log message moves too"""
        msg = self.mgr.get_log( 'myRenamedBranch' )
        self.assertEqual( '', msg, "empty log message" )

        self.mgr.put_log( BRANCH_NAME, 'This Is A Log' )
        msg = self.mgr.rename_branch( BRANCH_NAME, 'myRenamedBranch' )

        # The log belongs to the new name ...
        msg = self.mgr.get_log( 'myRenamedBranch' )
        self.assertEqual( 'This Is A Log', msg, "log message set" )
        # ... and not to the old name
        msg = self.mgr.get_log( BRANCH_NAME )
        self.assertEqual( '', msg, "empty log message" )



# --------------------------------------------------------------------

if __name__ == '__main__':
    unittest.main()
