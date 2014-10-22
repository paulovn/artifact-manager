# ********************************************************************** <====

from . import *
from artmgr.transport import *

# ********************************************************************** ====>

import os
import sys
import errno
import subprocess
import stat
import re
import ast
import hashlib
import glob
from datetime import datetime
from posixpath import join as posixjoin
from HTMLParser import HTMLParser
from ConfigParser import SafeConfigParser, NoSectionError, NoOptionError
from operator import itemgetter
from collections import defaultdict
from contextlib import closing

try:
    import cStringIO as StringIO
except ImportError:
    import StringIO


# ---------------------------------------------------------------------
        
def object_remote_location( name ):
    """Return the location of an object in the repository, as (path,basename)"""
    return (OBJECTS + '/' + name[:2], name[2:])


def _open_single_transport( url, subrepo, verbose ):
    """Open a transport to a remote repo"""
    #print url
    if( url.startswith('http:') or url.startswith('https:') ):
        return WebTransport( url, subrepo, verbose )
    elif( url.startswith('\\') or url.startswith('smb:') ):
        return SMBTransport( url, subrepo )
    else:
        return LocalTransport( url, subrepo )


def open_transports( spec, subrepo, write=False, verbose=0 ):
    """Open one (R) or two (R & R/W) transports to a remote repo"""
    spec = spec.split(',')
    reader = _open_single_transport( spec[0], subrepo, verbose )
    if not write:
        return reader
    if len(spec) == 1:
        spec.append( spec[0] )
    writer = _open_single_transport( spec[1], subrepo, verbose )
    return (reader,writer)


def write_options_to_cfg( obj, cfg ):
    """Convert the options stored in the object into a config object"""
    cfg.add_section( OPTIONS_SECTION )
    for n in DEFAULT_OPTIONS:
        cfg.set( 'general', n, str(getattr(obj,n)) )


def read_options_from_cfg( remote_cfg, command_line_options, obj ):
    """
    Insert config options into an object. First set from defaults, then
    override with the config of the remote repo, and finally override
    with command-line options
    """
    # Check version
    try:
        v = remote_cfg.getint(OPTIONS_SECTION,'VERSION') 
        if v > BACKEND_VERSION:
            raise InvalidArgumentError( 'incompatible repository version: '+str(v) )
    except NoSectionError:
        remote_cfg.add_section( OPTIONS_SECTION )
    except NoOptionError:
        pass
    # Fill in options
    for k in DEFAULT_OPTIONS:
        # Set default
        setattr(obj,k,DEFAULT_OPTIONS[k])
        # Override with remote config
        try:
            remote_value = remote_cfg.get(OPTIONS_SECTION,k)
            setattr( obj, k, ast.literal_eval(remote_value) )
        except NoOptionError:
            pass
        except (SyntaxError,ValueError) as err:
            raise TransportError( "Can't parse remote value for config option '"
                                  + k + "': " + remote_value )
        # Finally, override with a command-line argument if defined
        v = getattr(command_line_options,k,None)
        if v is not None:
            setattr(obj,k,v)
    

# ---------------------------------------------------------------------

def sha1_file( size, filename ):
    """Compute a hash over a file, using the same spec that Git uses"""
    s = hashlib.sha1()
    s.update("blob %u\0" % size)
    with open(filename,'rb') as f:
        while True:
            bytes = f.read(8192)
            if not bytes:
                break
            s.update(bytes)
    return s.hexdigest()  

def fix_path(path):
    """Normalize a local path, and ensure we use forward slashes"""
    result = os.path.normpath(path)
    if os.sep == '\\':
        result = result.replace('\\', '/')
    return result

def size_string(size):
    """Return a human-readable string for a size given in bytes"""
    suffixes = ['','K','M','G','T']
    suffixIndex = 0
    precision = int(size > 1048576)
    while size > 1024:
        suffixIndex += 1 #increment the index of the suffix
        size = size/1024.0 #apply the division
    return "%.*f%s"%(precision,size,suffixes[suffixIndex])

def item_string(entry,subdir,path=None):
    """
    Return the item description corresponding to an object, as a string
      @param entry (list): the object record, in the index
      @param subdir (str or None): an optional subdirectory to take out of the
        filename
      @param path (str): the filename to print (overrides the one in the index)
    """
    start = 0 if subdir is None else len(subdir)
    if path is None:
        path = entry[3]
    return '  %s %6s %s' % (datetime.fromtimestamp(entry[0]).strftime('%Y-%m-%d %H:%M %z'), size_string(entry[1]), path[start:] )

def dict_to_set( c ):
    """
    Convert a dict holding lists of strings into a set, 
    joining keys & values
    """
    if c is None:
        return set()
    return set( ((k,l) for k,v in c.iteritems() for l in v ) )


# ---------------------------------------------------------------------

def git_find_info( what, repo_dir ):
    """
    Find information about a git repository. Try first calling the git
    command line directly; if that fails search within git internals
    """
    class StrippedFile(file):
        """A small helper class to read a config file with leading spaces"""
        def readline(self):
            return super(StrippedFile, self).readline().strip()

    # Range of git commands we can execute
    commands = { 'remote' : ['git','config','--get', 'remote.origin.url'],
                 'branch' : ['git','rev-parse','--abbrev-ref','HEAD'],
                 'ignored' : ['git','ls-files','-o','-i', '--exclude-standard']
               }

    # Execute git. If that fails, try digging into .git repo dir directly
    try:

        cmd = commands[what]
        if sys.version_info < (2,7):
            r = subprocess.Popen(cmd,cwd=repo_dir,stdout=subprocess.PIPE).communicate()[0]
        else:
            r = subprocess.check_output(cmd,cwd=repo_dir)
        output = r.rstrip()

    except Exception as e:
        if hasattr(e,'errno') and e.errno == errno.ENOENT:
            raise InvalidArgumentError("can't find directory: '%s'" % repo_dir)
        elif what == 'ignored':
            raise InvalidArgumentError("can't use --git-ignored option: git execution failed: " + str(e) )

        try:
            if what == 'remote':
                c = SafeConfigParser()
                with StrippedFile(os.path.join(repo_dir,'.git','config')) as f:
                    c.readfp(f)
                    output = c.get('remote "origin"','url')
            else:       # what == 'branch'
                with open(os.path.join(repo_dir,'.git','HEAD')) as f:
                    data = f.readline().rstrip()
                return data.split('refs/heads/')[-1]
        except Exception as e:
            if hasattr(e,'errno') and e.errno == errno.ENOENT:
                raise InvalidArgumentError("can't find git metadata in '%s'" % repo_dir)

    # Terminate output parsing
    if what == 'remote':
        (head,tail) = output.split(':')
        (repo_name,ext) = os.path.splitext( tail )
        return repo_name
    elif what == 'ignored':
        return output.splitlines()
    else:
        return output


# ---------------------------------------------------------------------


class ArtifactReader( object ):
    """
    A class to manage a remote artifact repository, only for read operations
    (list remote listings, check against local artifacts, sync local with 
    remote by downloading, get individual artifacts)
    """

    def __init__(self, options ):
        # Store some generic options
        self.verbose = options.verbose
        self.dry_run = options.dry_run
        self.subdir = options.subdir
        # Store the repository configuration from the options
        self._repo_config( options )
        # Fetch remote lists
        self.remote_branches = self._get_all_branches() # name : logmsg
        self.remote_index = self._get_index()           # sha : [object spec]
        # Initialize local lists
        self._reset_lists()

    def _reset_lists( self ):
        self.local_index = None                         # sha : [object spec]
        self.local_artifacts = None                     # sha : [list of files]

    def _repo_connect( self, source, subrepo ):
        """Open transport for reading"""
        self.reader = open_transports( source, subrepo )
        

    def _repo_config( self, options ):
        """Prepare the configuration for the remote artifact repository"""
        # Open the remote repository
        self._repo_connect( options.server_url, options.repo_name )
        # Read remote options
        config = SafeConfigParser()
        if not self.reader.exists( OPTIONS ):
            if self.verbose:
                print "Warning: repository",options.repo_name,"not initialized"
        else:
            with closing(StringIO.StringIO()) as buffer:
                self.reader.get( OPTIONS, buffer )
                buffer.seek( 0 )
                config.readfp( buffer )
        # Set the options, from defaults, remote config and command-line
        read_options_from_cfg( config, options, self )
        #print self.__dict__


    def _get_index( self ):
        """Get the index of the remote repository"""
        index = {}
        if self.reader.exists( INDEX ):
            with closing(StringIO.StringIO()) as buffer:
                self.reader.get( INDEX, buffer )
                for line in buffer.getvalue().splitlines():
                    data = line.split(' ',4)
                    index[ data[0] ] = [ float(data[1]), int(data[2]), 
                                         int(data[3],8), data[4] ]
        return index


    def _get_all_branches( self, get_logs=False ):
        """Get the list of branches in the remote repository"""
        branchlist = set()
        if self.reader.exists( BRANCHES ):
            with closing(StringIO.StringIO()) as buffer:
                self.reader.get( BRANCHES, buffer )
                branchlist.update( buffer.getvalue().splitlines() )
        branches = {}
        if not self.reader.exists(LOGS) or not get_logs:
            return dict( [(b,'') for b in branchlist] )
        else:
            return dict( [(b,self.get_log(b)) for b in branchlist] )


    def get_log( self, branch_string, return_none=False ):
        """Get the log message for a branch"""
        name = LOGS + '/' + branch_string
        if not self.reader.exists( name ):
            return ''
        with closing(StringIO.StringIO()) as buffer:
            self.reader.get( name, buffer )
            data = buffer.getvalue()
        return data


    def get_branch( self, branch_string, return_none=False ):
        """
        Get the list of artifacts in the remote repo that correspond to a given 
        branch
          @param branch_string (str): name of the branch to fetch
          @param return_none (bool): to return \c None if the branch does
            not exist (otherwise an exception is raised)
          @return (dict): all files in the branch, as a \t (key,path) dict
        """
        name = REFS + '/' + branch_string
        # Check the branch does exist
        if return_none and not self.reader.exists( name ):
            if self.verbose:
                print "Warning: branch '%s' not in remote repo" % branch_string
            return None
        # Read the branch list from the server
        with closing(StringIO.StringIO()) as buffer:
            r = self.reader.get( name, buffer )
            data = buffer.getvalue()
        # Construct the branch dict
        branch = defaultdict(list)
        prev = None
        for l in data.splitlines():
            f = l.split(' ',2)
            key = f[0]
            value = f[1] if len(f)>1 else self.remote_index[key][3]
            if key != '-':
                branch[key].append( value )
            else:
                if prev is None:
                    print "Error in remote repo: invalid branch spec for '%s'" % branch_string
                    return None
                branch[prev].append( value )
            prev = key

        return branch
        

    def list_branches( self, current_branch='', logs=False ):
        """
        Print out the list of branches in the remote repo
        """
        if self.verbose:
            if self.verbose > 1:
                print "\n# Info: list remote branches"
            if logs:
                self.remote_branches = self._get_all_branches( True )
            for b in sorted(self.remote_branches.keys()):
                print '*' if b == current_branch else ' ',
                print b if not logs else "%s : %s\n" % (b, self.remote_branches[b])
        return self.remote_branches.keys()


    def list_artifacts( self, branch_string, local_basedir ):
        """
        Print out the list of artifacts in the remote repo that
        correspond to a given branch
        """
        if branch_string == '.':        # gather local artifacts
            self._local_collect_list( local_basedir )
            clist = self.local_artifacts
            index = self.local_index
        elif branch_string is None:
            clist = dict( [(k,[self.remote_index[k][3]])
                          for k in self.remote_index.iterkeys()] )
            index = self.remote_index
        else:                           # gather remote artifacts
            clist = self.get_branch( branch_string, return_none=True )
            index = self.remote_index

        if clist is None:
            return False

        if self.verbose:
            print "\n# Info: list",
            if branch_string == '.':
                print "local artifacts"
            elif branch_string is None:
                print "remote artifacts across all branches"
            else:
                print "remote artifacts for '%s'" % branch_string

        # List all items. Sort by name (first instance), then by date
        for k,v in sorted( clist.iteritems(), 
                           key = lambda e : (e[1],index[e[0]][0]) ):
            if self.subdir and not v[0].startswith(self.subdir):
                continue
            print item_string(index[k],self.subdir,v[0])
            for item in v[1:]:
                print '  %49s' % item 

        return True


    def _add_local_file( self, name, size=None ):
        """Add a local artifact file to our internal tables"""
        if size is None:
            size = os.path.getsize(name)
        visible_name = os.path.join(self.subdir,name) if self.subdir else name
        s = [os.path.getmtime(name), size, 0644, visible_name]
        k = sha1_file(size,name)
        self.local_index[k] = s
        self.local_artifacts[k].append( visible_name )


    def _local_collect_list( self, local_basedir, reload=False ):
        """
        Get all artifacts in the local checked out repository, and populate 
        the object's structure
        """
        if self.local_artifacts is not None and not reload:
            return
        self.local_index = {}                           # sha : [object spec]
        self.local_artifacts = defaultdict( list )      # sha : [list of files]
        current = os.getcwd()
        os.chdir( local_basedir )
        try:
            if self.git_ignored:
                for fullname in git_find_info( 'ignored', '.' ):
                    self._add_local_file( fullname )
                return

            # Compile extensions
            artifact_ext = set( map(lambda s : s.lower() if s.startswith('.') 
                                    else '.'+s.lower(), 
                                    self.extensions) )

            # Add all full paths (taking care of expanding globs)
            full_files = set()
            for f in self.files:
                if any( c in f for c in '*?[]' ):
                    full_files.update( glob.glob(f) )
                else:
                    full_files.add( f )

            # Traverse the tree and add all matching files
            for root, dirs, files in os.walk( '.' ):

                # Remove the directory with the Git metadata
                try:
                    dirs.remove( '.git' )
                except ValueError:
                    pass

                # Push all the files that match the conditions
                for name in files:
                    fullname = fix_path( os.path.join(root,name) )
                    if os.path.islink( fullname ):
                        continue        # skip symbolic links to files

                    # Build the set of extensions for this file
                    e = name.lower().split(os.path.extsep)[1:]
                    ext = set( [ '.' + os.path.extsep.join(e[i:]) 
                                 for i in range(0,len(e)) ])

                    size = os.path.getsize(fullname)
                    #print fullname, ext, size

                    if (fullname in full_files or 
                        (not artifact_ext.isdisjoint(ext) and 
                         size > self.min_size)):
                        self._add_local_file( fullname, size )
        finally:
            os.chdir( current )


    def _compare_lists( self, collection1, collection2 ):
        """
        Compare two dicts of items. Use both the key (i.e. the SHA1 hash) and
        the value (i.e. the path) in the comparison. This way we check both file
        contents and file location.
        """
        c1 = dict_to_set( collection1 )
        c2 = dict_to_set( collection2 )
        both = c1 & c2
        only_c1 = c1 - c2
        only_c2 = c2 - c1
        #import pprint; pprint.pprint(c1); pprint.pprint(c2)
        return (both, only_c1, only_c2)


    def local_check_list( self, local_basedir, branch_string ):
        """
        Compare the local artifacts with the ones in the remote repo,
        and return the differences
          @param local_basedir (str): the name of the local folder
          @param branch_string (str): identifier for the branch in remote repo
          @return a tuple of \t (<result_lists>,<artifact_index>), where
             <result_lists> contains three lists:
               (<same files>, <files only in local>, <files only in remote>)
        """
        # Compose dicts for local files & remote files
        self._local_collect_list( local_basedir )
        #local_dict = dict([(k,v[3]) for k,v in self.local_artifacts.iteritems()])
        remote_dict = self.get_branch( branch_string, return_none=True )

        # Compare those dicts
        results = self._compare_lists( self.local_artifacts, remote_dict )

        # Prepare a dictionary containing all local & remote items
        # -- first put all local files
        all_artifacts = self.local_index.copy()
        # -- now add all remote artifacts that are not in local
        all_artifacts.update( dict( (item[0],self.remote_index[item[0]]) 
                                    for item in results[2] ) )

        return (results,all_artifacts)


    def _print_diff( self, lists, index ):
        """
        Print out lists of item differences
         @param lists (dict): the lists to print, indexed by name
         @param index (dict): the index containing all items in the lists
        """
        for lnam,lval in lists.iteritems():
            if not lval:
                continue # empty list; do not print
            #import pprint; pprint.pprint(lval)
            # build the list of items, remmoving all not in selected subdir
            item_list = [ i for i in sorted( lval, key=itemgetter(1) )
                          if not self.subdir or i[1].startswith(self.subdir) ]
            if not item_list:
                continue # if none left, skip list
            print '**', lnam
            for i in item_list:
                print item_string( index[i[0]], self.subdir, i[1] )


    def _print_diff_old( self, results, names=('ok','LOC','SRV') ):
        """
        Print out the list of item differences
        Old listing format, with a single combined list labeled by status
        """
        status = {}
        for r in zip(results,names):
            status.update( dict( (item,r[1]) for item in r[0] ) )
        for k in sorted( status, key=itemgetter(1) ):
            print '%4s  %s' % (status[k], k[1] )


    def diff( self, branch1, branch2, show_all ):
        """
        Compare two branches, and print out the differences
          @param branch1 (str): the name of the 1st branch
          @param branch2 (str): the name of the 2nd branch
        """
        list1 = self.get_branch( branch1, return_none=True )
        list2 = self.get_branch( branch2, return_none=True )
        results = self._compare_lists( list1, list2 )
        if self.verbose > 1:
            subd = " for subdir '%s'" % self.subdir if self.subdir else ''
            print "\n# Info: compare branches '%s' & '%s'%s" % (branch1,branch2,subd)
        lists = dict( zip( ('in both','only in '+branch1,'only in '+branch2),
                           results ) )
        if not show_all:
            del lists['in both']

        # Print the lists
        if self.verbose:
            self._print_diff( lists, self.remote_index )
        return lists


    def local_print_changes( self, local_basedir, branch_string, show_all ):
        """
        Print out a summary of the comparison between the local artifacts 
        and the contents in the remote repo
        """
        results, artifacts = self.local_check_list(local_basedir,branch_string)
        if self.verbose > 1:
            print "\n# Info: check local artifacts against '%s'" % branch_string
            if self.subdir:
                print "# for subdir '%s'" % self.subdir

        # Do the old listing format (single-list)
        #self._print_diff_old( results )
        #return True

        # Make the lists we will print
        lists = dict( zip( ('in both','only in local','only in server'),
                           results ) )
        if not show_all:
            del lists['in both']

        # Print the lists
        if self.verbose:
            self._print_diff( lists, artifacts )
        return lists


    def _get_file( self, fileid, outname ):
        """
        Download an artifact into a local file
        """
        # Create the directory to put the file, if needed
        (head,tail) = os.path.split( outname )
        if head:
            mkpath_recursive( head )
        # Download the file
        source_path = posixjoin( *object_remote_location(fileid) )
        with open(outname,'wb') as f:
            self.reader.get( source_path, f )
        # Set permissions & modification time
        filedata = self.remote_index[fileid]
        os.chmod( outname, int(filedata[2]) )
        os.utime( outname, (-1, float(filedata[0])) )


    def download_artifacts( self, branch_string, local_basedir, 
                            remove_old=False ):
        """
        Download to the local folder all artifacts in remote repo that
        correspond to a given branch.
          @param local_basedir (str): the name of the local folder
          @param branch_string (str): identifier for the branch in remote repo
          @param remove_old (bool): whether to delete local artifact files not
            in the remote repo
        """
        if self.verbose > 1:
            print "\n# Info: download artifacts for '%s'" % branch_string
            if self.subdir:
                print "# for subdir '%s'" % self.subdir
            if self.dry_run:
                print "** DRY RUN"

        # If the branch does not exist, we cannot proceed
        if branch_string not in self.remote_branches:
            if self.verbose:
                print "Branch '%s' does not exist in artifact repo" % branch_string
            return False

        # Get the lists of files, compose status for each file
        results, artifacts = self.local_check_list(local_basedir,branch_string)
        status = {}
        for r in zip(results,('ok','old','new')):
            status.update( dict( (item,r[1]) for item in r[0] ) )
            
        # Go over each artifact and perform the required action
        prefix = len(self.subdir) if self.subdir else None
        downloaded = 0
        for k in sorted( status, key=itemgetter(1) ):

            if prefix is None:
                outname = k[1]
            elif k[1].startswith( self.subdir ):
                outname = k[1][prefix:]
            else:
                continue

            what = status.get(k)
            action = '' if self.dry_run else "[DOWN]" if what == 'new' else "[DEL]" if what == 'old' and remove_old else ''
            if self.verbose:
                print '%4s: %s %s' % (what, outname, action)
            if action == '[DOWN]':
                self._get_file( k[0], os.path.join(local_basedir,outname) )
                downloaded += 1
            elif action== '[DEL]':
                os.unlink( os.path.join(local_basedir,outname) )

        return downloaded


    def get( self, filename, branch, outname ):
        """
        Fetch a file from a branch in remote repo
        """
        if self.verbose > 1:
            print "\n# Info: download remote artifact '%s' @ '%s'" % (filename,branch)
            if self.dry_run:
                print "** DRY RUN"
        files = self.get_branch( branch, return_none=True )
        if files is None:
            print "Error: no files in branch '%s'" % branch
            return False        
        for k,v in files.iteritems():
            if v == filename:
                if not self.dry_run:
                    if self.verbose:
                        print "[DOWNLOADING]"
                    self._get_file( k, outname )
                return True
        print "Error: can't find the file in branch '%s'" % branch
        return False
                

    def get_cfg( self ):
        """
        Get the options in the remote repo
        """
        cfg = SafeConfigParser()
        write_options_to_cfg( self, cfg )
        if self.verbose:
            print "\n# Info: get options from remote repo"
        cfg.write( sys.stdout )





