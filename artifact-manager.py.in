#!/usr/bin/env python

"""
A script to manage a remote repository for overlaying artifacts (binary files) 
on top of a local folder (typically a checked-out Git local repository, but
not necessarily). Enables keeping versioned sets of artifacts, with their
position in the local tree, so that they can be downloaded, uploaded and
compared across versions.

Accepts as transport layers:
  - HTTP for read-only operations (listing/downloading) artifacts
  - a locally visible folder for R/W operations (above, plus uploading and
    version management)
  - An SMB R/W transport is in the works

"""

APP_VERSION = '2.0'

# Default URLs for the artifacts repository (as R & R/W transports)
#REPO_URL = ('http://artifacts.hi.inet',r'\\oriente.hi.inet\artifacts')

# Default URLs for the artifactory repository (as R & R/W transports)
# The R/W transport is assumed to be locally mounted
REPO_URL = ('http://artifactory.hi.inet/artifactory/misc-opengvp',
            '/mnt/artifactory')


# ********************************************************************** <====

import sys
import os.path
sys.path.append( os.path.join(os.path.dirname(__file__),'lib') )

from artmgr import DEFAULT_OPTIONS, WHEREAMI
from artmgr.reader import ArtifactReader, git_find_info
from artmgr.manager import ArtifactManager

# ********************************************************************** ====>

import argparse

if __name__ == "__main__":

    # Generic arguments
    gnric = argparse.ArgumentParser( add_help=False )
    gnric.add_argument('--verbose', '-v', type=int, default=2, help='verbose mode (0-2), default: %(default)d')
    gnric.add_argument('--dry-run', action='store_true', help="don't modify files, locally or remotely" )
    gnric.add_argument('--server-url', '-u', default=','.join(REPO_URL),
    help='Base URL for the repository server (default: %(default)s)' )
    gnric.add_argument('--repo-name', '-r', help='set the name of repository to use from the server' )
    gnric.add_argument('--branch', '-b', help='set the name of the branch to operate with' )
    gnric.add_argument('--subdir', '-s', help='operate only on a subdir of the project' )
    gnric.add_argument('--project-dir', '-d', default=os.getcwd(), help='local folder to use as tree root (default: %(default)s)')

    gnric.add_argument('--extensions', '-e', help='extensions to consider as artifacts (default: '+','.join(DEFAULT_OPTIONS['extensions'])+')', default=None )
    gnric.add_argument('--files', '-f', help='files to add explicitly as artifacts (full path within the project)', metavar="FILE", default=None, nargs='+' )
    gnric.add_argument('--min-size', type=int, help='minimum size in bytes of an artifact to be considered (default: ' +str(DEFAULT_OPTIONS['min_size'])+')', default=None )
    gnric.add_argument('--git-ignored', action='store_true', help='define as artifacts all files ignored by git in the local repo' )


    # Define & read command-line options
    parser = argparse.ArgumentParser( description="Manage binary artifacts against a versioned remote repository (v. "+APP_VERSION+"). See " + WHEREAMI)
    subp = parser.add_subparsers( dest='command', title='command',
                                  help='Use -h on the command for additional options')

    s1 = subp.add_parser( 'list', help='list the artifacts in remote repo', 
                          parents=[gnric] )
    s1.add_argument('--show-all', '-a', action='store_true',
                    help='list artifacts in all branches')

    s2 = subp.add_parser( 'diff', help='compare two artifact lists',
                          parents=[gnric]  )
    s2.add_argument('other_branch', metavar='other-branch', nargs='?',
                    help='name of the other branch to compare to, when not the local project dir' )
    s2.add_argument('--show-all', '-a', action='store_true',
                    help='show all files, not only the differences' )

    s4 = subp.add_parser( 'download', help='download artifacts from server into the local project dir', parents=[gnric]  )
    s4.add_argument('--delete-local', action='store_true', help='when downloading, remove from local directory the artifacts not present in the remote side (default: %(default)s)' )
    
    s5 = subp.add_parser( 'get', help='fetch a single artifact file from remote server', parents=[gnric]  )
    s5.add_argument( 'name', help='file to fetch' ) 
    s5.add_argument('--outname', '-o', help='output file name, when not the same name as the original file' )

    s6 = subp.add_parser( 'upload', help='upload the set of local artifacts to the current branch in remote repo', parents=[gnric]  )
    s6.add_argument('--overwrite', action='store_true', help='when uploading, overwrite the remote artifact definition for the current branch (default: %(default)s)' )

    s7 = subp.add_parser( 'branches', help='list all branches in remote repo',
                          parents=[gnric] )
    s7.add_argument('--log', '-l', action='store_true',
                     help='show branch log messages' )

    s8 = subp.add_parser( 'getoptions', parents=[gnric],
                          help='get configuration options from remote repo' )
    s9 = subp.add_parser( 'setoptions', parents=[gnric],
                          help='set configuration options in remote repo' )

    s10 = subp.add_parser( 'rename-branch', parents=[gnric],
                           help='rename a branch in remote repo' )
    s10.add_argument('new_name', metavar='new-name', 
                     help='new name of the branch' )

    s11 = subp.add_parser( 'getlog', parents=[gnric],
                           help='get the log message for this branch' )

    s12 = subp.add_parser( 'setlog', parents=[gnric],
                           help='set the log message for this branch' )
    s12.add_argument('msg', help='text for the log message' )


    args = parser.parse_args()
    #print args

    # If not given, find out the name of the repository & branch from the
    # name of the git repo checked out in the local folder, and the
    # current checked out branch
    if not args.repo_name:
        args.repo_name = git_find_info( 'remote', args.project_dir )
    if not args.branch:
        args.branch = git_find_info( 'branch', args.project_dir )
    #print args

    if args.subdir and not args.subdir.endswith('/'):
        args.subdir += '/'

    # Split extensions
    if args.extensions == '':
        args.extensions = []
    elif args.extensions is not None:
        args.extensions = args.extensions.split(',')

    # Instantiate the manager class
    mgr_class = ArtifactManager if args.command in ('upload','setoptions','rename-branch','setlog') else ArtifactReader
    mgr = mgr_class( args )

    # Do the operation
    if args.command == 'list':

        b = args.branch if not args.show_all else None
        r = mgr.list_artifacts( b, args.project_dir )

    elif args.command == 'branches':

        r = mgr.list_branches( args.branch, args.log )

    elif args.command in ('diff','check'):

        if args.other_branch:
            l = mgr.diff( args.branch, args.other_branch, args.show_all )
        else:
            l = mgr.local_print_changes( args.project_dir, args.branch, 
                                         args.show_all )
        # Exit code is the number of elements in the lists
        r = sum( [ len(k) for k in l.itervalues() ] )

    elif args.command == 'download':

        r = mgr.download_artifacts( args.branch, args.project_dir, 
                                    args.delete_local )

    elif args.command == 'get':

        if args.outname is None:
            args.outname = os.path.join( args.project_dir, args.name )
        r = mgr.get( args.name, args.branch, args.outname )

    elif args.command == 'upload':

        r = mgr.upload_artifacts( args.project_dir, args.branch, args.overwrite ) 

    elif args.command == 'comment':

        r = mgr.set_comment( args.branch, args.overwrite ) 

    elif args.command == 'setoptions':

        r = mgr.put_cfg()

    elif args.command == 'getoptions':

        r = mgr.get_cfg()

    elif args.command == 'getlog':

        if args.verbose:
            print "\n# Info: log message for branch '%s'" % args.branch
        msg = mgr.get_log( args.branch )
        print msg if len(msg) else "[no log]"
        r = 0

    elif args.command == 'setlog':

        r = mgr.put_log( args.branch, args.msg )

    elif args.command == 'rename-branch':

        r = mgr.rename_branch( args.branch, args.new_name )

    else:

        print args.command, "not implemented yet"
        sys.exit(1)


    # Exit with an appropriate exit code
    out = r is False
    sys.exit( out )
