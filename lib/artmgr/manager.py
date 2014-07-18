# ********************************************************************** <====

from artmgr import *
from artmgr.reader import ArtifactReader, object_remote_location, open_transports, write_options_to_cfg

# ********************************************************************** ====>


import os
import sys
import errno
import stat
import re
import glob
from datetime import datetime
from posixpath import join as posixjoin
from HTMLParser import HTMLParser
from ConfigParser import SafeConfigParser, NoSectionError, NoOptionError
from collections import defaultdict
from contextlib import closing

try:
    import cStringIO as StringIO
except ImportError:
    import StringIO



# ---------------------------------------------------------------------

class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

def strip_tags(html):
    """A function to remove all HTML tags from a text buffer"""
    s = MLStripper()
    s.feed(html)
    return s.get_data()


# ---------------------------------------------------------------------

class ArtifactManager( ArtifactReader ):
    """
    A class to manage a remote artifact repository, for both read
    operations (download artifacts, check & compare artifact listings)
    and write operations (initialize, upload artifacts)
    """

    def __init__( self, options ):
        # Parent constructor will read the remote repository metadata
        super(ArtifactManager,self).__init__( options )
        # Now initialize the repository if it happens to be empty
        if not self.writer.exists( INDEX ) and not self.dry_run:
            self.repo_init( options )

    def _repo_connect( self, source, subrepo ):
        """Open transports for R/W"""
        (self.reader,self.writer) = open_transports( source, subrepo, 
                                                     write=True )

    def repo_init( self, options ):
        """
        Initialize a new repository: write the folders and initial files
        """
        if self.verbose:
            print "\n# Info: initializing repository",options.repo_name
        # Ensure the base folder for the repo is there
        self.writer.init_base()
        # Create the needed subfolders
        self.writer.folder_create( OBJECTS )
        self.writer.folder_create( REFS )
        # Create README, index & options files
        with closing(StringIO.StringIO(README)) as buffer:
            self.writer.put( buffer, 'README.html' )
        with closing(StringIO.StringIO(strip_tags(README))) as buffer:
            self.writer.put( buffer, 'README' )
        self.writer.put( StringIO.StringIO(), INDEX )
        self.put_cfg()


    def put_cfg( self ):
        """Write the config options file in the remote repo"""
        cfg = SafeConfigParser()
        write_options_to_cfg( self, cfg )
        if self.verbose:
            print "\n# Info: setting repository options in remote server"
            cfg.write( sys.stdout )
        if self.dry_run:
            print "** DRY RUN"
            return
        with closing(StringIO.StringIO()) as buffer:
            cfg.write( buffer )
            buffer.seek( 0 )
            self.writer.put( buffer, OPTIONS )

    def put_object( self, data_source, object_name ):
        dest_path = object_remote_location(object_name)
        self.writer.folder_ensure( dest_path[0] )
        self.writer.put( data_source, posixjoin(*dest_path) )

    def put_log( self, branch_string, msg ):
        """Set the log message for a branch"""
        dest_name = os.path.join( LOGS, branch_string )
        (head,tail) = os.path.split( dest_name )
        if head:
            self.writer.folder_ensure( head )
        with closing(StringIO.StringIO(msg)) as buffer:
            self.writer.update( buffer, dest_name )
        
    def _put_branch_filelist( self, branch_string ):
        """Put in the remote repository the list of objects for one branch"""
        # Compose the final name & ensure the destination folder exists
        dest_name = os.path.join( REFS, branch_string )
        (head,tail) = os.path.split( dest_name )
        if head:
            self.writer.folder_ensure( head )
        # Construct the file list
        if self.version < 3:
            files = ( k for k in sorted(self.local_index.keys()) )
        else:
            files = list()
            for k,v in self.local_artifacts.iteritems():
                files.append( '%s %s' % (k,v[0]) )
                for a in v[1:]:
                    files.append( '- ' + a )
        # write it
        with closing(StringIO.StringIO( "\n".join(files) )) as buffer:
            self.writer.update( buffer, dest_name )


    def _put_index( self ):
        buffer = StringIO.StringIO()
        for item in sorted(self.remote_index):
            v = self.remote_index[item]
            buffer.write( "{0} {1} {2} 0{3:o} {4}\n".format( item, *v ) )
        self.writer.update( StringIO.StringIO(buffer.getvalue()), INDEX )


    def rename_branch( self, branch, new_branch_name ):
        """Rename a branch in the remote server"""
        if branch not in self.remote_branches:
            print "Branch '%s' does not exist in artifact repo" % branch
            return False
        if self.verbose:
            print "\n# Info: Renaming branch '%s' to '%s'" % (branch,new_branch_name)
        if self.dry_run:
            return 
        # Rename the branch filelist
        oldname = os.path.join( REFS, branch )
        newname = os.path.join( REFS, new_branch_name )
        (head,tail) = os.path.split( newname )
        if head:
            self.writer.folder_ensure( head )
        self.writer.rename( oldname, newname )
        # Transfer the log message, if needed
        log = self.get_log( branch )
        if log:
            newlog = os.path.join(LOGS,new_branch_name)
            self.writer.folder_ensure( os.path.split(newlog)[0] )
            self.writer.rename( os.path.join(LOGS,branch), newlog )
        # Update the list of branches
        del self.remote_branches[branch]
        self.remote_branches[new_branch_name] = log
        self.put_branches_list()
        return True


    def put_branches_list( self ):
        """Write in the remote repo the list of existing branches"""
        buffer = StringIO.StringIO()
        buffer.write( "\n".join(sorted(self.remote_branches.keys())) )
        self.writer.update( StringIO.StringIO(buffer.getvalue()), BRANCHES )


    def upload_artifacts( self, local_basedir, branch_string, overwrite=False ):
        """
        Upload all artifacts in the local directory to the remote repository
          @param local_basedir (str): local directory containing artifacts
          @param branch_string (str): identifier for the branch to upload to
          @param overwrite (bool): if the branch already exists in the
            remote repository, upload will fail unless this is \c True
          @return (int): nnumber of uploaded files
        """
        # Check if this branch already has a remote entry, and bark if so
        # and we're not in overwrite mode
        remote = self.get_branch( branch_string, return_none=True )
        if remote is not None and not overwrite:
            if self.verbose:
                print "Error: branch", branch_string, "already exists in repository"
                print "Use --overwrite option to change it"
            return False
        # Collect all local artifact object & find out which ones are not yet 
        # in the remote side.
        self._local_collect_list( local_basedir )
        newf = dict( (sha,self.local_artifacts[sha])
                     for sha in self.local_artifacts 
                     if sha not in self.remote_index )
        if self.verbose > 1:
            print "\n# Info: Uploading local artifacts to '%s'" % branch_string
            print "  total local artifacts: ", len(self.local_artifacts)
            print "  already in repo: ", len(self.local_artifacts) - len(newf)
            if self.dry_run: print "  ** DRY RUN"
            #print self.local_artifacts
        # Process each new file
        uploaded = 0
        for k,v in newf.iteritems():
            if self.verbose:
                print "   ... uploading: ", ' '.join(v)
            if self.dry_run:
                continue
            # Send it to remote repo & add locally to index
            # Use just the 1st file (the same "object" may be in more than 
            # one position locally)
            with open( os.path.join(local_basedir,v[0])) as f:
                self.put_object( f, k )
            self.remote_index[k] = self.local_index[k]
            uploaded += 1

        # Now upload the list of files for this branch and update remote indices
        if not self.dry_run:
            self._put_branch_filelist( branch_string )
            if branch_string not in self.remote_branches.keys():
                self.remote_branches[branch_string] = ''
                self.put_branches_list()
            if len(newf):
                self._put_index()

        return uploaded




