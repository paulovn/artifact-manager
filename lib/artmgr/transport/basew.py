# ********************************************************************** <====

from .. import InvalidArgumentError, TransportError

# ********************************************************************** ====>

import os.path


            
# ---------------------------------------------------------------------
# Read-write transports inherit from BaseWTransport. They need to support:
#  * get
#  * otype
#  * init_base
#  * put
#  * delete
#  * rename
#  * folder_create


class BaseWTransport( object ):
    """
    A parent class providing some common functionality for R/W tranports
    """

    def folder_ensure( self, folder ):
        """Ensure a path exists in the repository. Create it if not"""
        if not folder:
            raise InvalidArgumentError('empty folder')
        t = self.otype( folder )
        if t == 'D':
            return
        elif t == 'F':
            raise TransportError( "can't make folder: %s is a file" % folder )
        (parent,name) = os.path.split( folder )
        if parent:
            self.folder_ensure( parent )
        self.folder_create( folder )

    def exists( self, path ):
        """
        Test if a path exists in the repository
        """
        check = self.otype( path )
        return check in ('F','D')

    def update( self, source, destname ):
        """
        Create or update a file in the repository, as atomically as possible
        """
        self.put( source, destname + '.new' )
        self.rename( destname + '.new', destname )

