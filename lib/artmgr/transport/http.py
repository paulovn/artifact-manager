import os
import sys
import errno
import urllib2
from posixpath import join as posixjoin


# ********************************************************************** <====

from .. import TransportError

# ********************************************************************** ====>


# ---------------------------------------------------------------------
# Read-only transports need to support two methods:
#  * exists
#  * get        

class WebTransport( object ):
    """
    A read-only transport using HTTP to access a remote repository
    """
    def __init__(self, url_base, subrepo='', verbose=0):        
        self._verbose = verbose
        self._base = posixjoin( url_base, subrepo )
        if not self._base.endswith('/'):
            self._base += '/'

    def exists( self, path ):
        """
        Test if a path exists in the repository, by sending a HEAD request
          @return (bool): \c True or \c False depending on the status received
            from the server
          @except TransportError on any access errors other than a 404
            (Not Found) status code.
        """
        url = self._base + path
        request = urllib2.Request(url)
        request.get_method = lambda : 'HEAD'
        try:
            response = urllib2.urlopen(request)
            return True
        except ValueError as e:
            raise TransportError( "can't access '%s' : invalid url" % url )
        except urllib2.HTTPError as e:
            if e.code == 404:
                return False
            raise TransportError( "can't access '%s' (%d): %s" % 
                                  (url,e.code,str(e.reason)) )
        except urllib2.URLError as e:
            raise TransportError( "can't access '%s' : %s" % 
                                  (url,str(e.reason)) )


    def get( self, source_name, dest ):
        """
        Get a file given its path, and store its contents in the 
        file-like object given.
        Any HTTP access or fetch error will generate an exception. To
        ensure the file is there before trying, use the exists() method.
        """
        u = urllib2.urlopen( self._base + source_name )
        meta = u.info()
        file_size = int(meta.getheaders("Content-Length")[0])
        file_name = source_name.split('/')[-1]
        if self._verbose > 1:
            print " .. downloading: %40s    size: %s" % (file_name, file_size)

        file_size_dl = 0
        block_sz = 8192
        while True:
            buffer = u.read(block_sz)
            if not buffer:
                break
            file_size_dl += len(buffer)
            dest.write(buffer)
            #status = r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
            #status = status + chr(8)*(len(status)+1)
            #print status,

            
