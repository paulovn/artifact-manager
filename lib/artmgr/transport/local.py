# ********************************************************************** <====

from artmgr.transport.basew import BaseWTransport

# ********************************************************************** ====>

import os
import sys
import errno
import stat
import re


# ---------------------------------------------------------------------

def mkpath_recursive(path):
    """Test a local path and, if it does not exist, create it recursively"""
    try:
        mode = os.stat( path ).st_mode
        if not stat.S_ISDIR(mode):
            raise InvalidArgumentError("parent path '"+str(path)+"' not a dir")
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise
        (head,tail) = os.path.split( path )
        if head:
            mkpath_recursive( head )
        os.mkdir( path )


# ---------------------------------------------------------------------


class LocalTransport( BaseWTransport ):
    """
    A full R/W transport instance that uses a locally visible directory to 
    store and read all artifact data
    """

    def __init__( self, basedir, subrepo ):
        """
        Constructor
          @param basedir (str): local folder to use
          @param subrepo (str): name of the repository we are dealing with
        """
        if not basedir:
            raise InvalidArgumentError("Empty basedir in local transport")
        if not subrepo:
            raise InvalidArgumentError("Empty subrepo in local transport")
        self._basedir = os.path.join(basedir,subrepo)
        super(LocalTransport,self).__init__()

    def init_base( self ):
        """Ensure the base path for the repository exists"""
        mkpath_recursive( self._basedir )
        

    def get( self, sourcename, dest ):
        """
        Read a file into a file-like destination.
        @param sourcename (str): name of the file in remote repo
        @param dest (file): an object with a write() method
        @return (bool): \c True if ok, \c False if the file does not exist
        """
        name = os.path.join(self._basedir,sourcename)
        try:
            with open(name, 'rb') as f:
                while True:
                    bytes = f.read( CHUNK )
                    if not bytes:
                        break
                    dest.write( bytes )
            return True
        except IOError as e:
            if e.errno == errno.ENOENT:
                return False
            raise
        
    def otype( self, path ):
        """
        Given the path of am object, return:
          * 'F' for a file, 
          * 'D' for a directory,
          * \c None if the path does not exist
        """
        oldname = os.path.join(self._basedir,path)
        try:
            mode = os.stat( oldname ).st_mode
        except OSError as e:
            if e.errno == errno.ENOENT:
                return None
            raise
        return 'D' if stat.S_ISDIR(mode) else 'F' if stat.S_ISREG(mode) else '?'

    def put( self, source, destname ):
        """
        Store a file. If a file with the same name existed, it is overwritten
        @param source (file): an object with a read() method
        @param destname (str): name of the destination file,
        relative to repo base directory
        """
        name = os.path.join(self._basedir,destname)
        with open(name, 'wb') as f:
            while True:
                bytes = source.read( CHUNK )
                if not bytes:
                    break
                f.write( bytes )

    def delete( self, filename ):
        """
        Delete a file
        """
        name = os.path.join(self._basedir,filename)
        os.unlink( name )

    def rename( self, oldname, newname ):
        """
        Rename a file into a new name and/or folder
        """
        oldname = os.path.join(self._basedir,oldname)
        newname = os.path.join(self._basedir,newname)
        os.rename( oldname, newname )

    def folder_create( self, path ):
        """
        Make a folder in the repository, assuming all parent folders exist
        """
        os.mkdir( os.path.join(self._basedir,path) )

    def folder_list( self, path ):
        """
        Return the list of all components (files & folders) in a folder
        *This method is optional*
        """
        return os.listdir( os.path.join(self._basedir,path) )


