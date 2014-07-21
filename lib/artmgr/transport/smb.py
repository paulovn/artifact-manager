# ********************************************************************** <====

from artmgr.transport.basew import BaseWTransport

# ********************************************************************** ====>

import os
import sys
import errno
import stat
import re
import getpass

from datetime import datetime
from socket import gethostname, gethostbyname

try:
    import smb.SMBConnection
    from nmb.NetBIOS import NetBIOS
    from mySMB import mySMBConnection
except ImportError:
    pass



# ---------------------------------------------------------------------

def parse_unc( unc, subpath ):
    """
    Parse a Windows UNC path, possibly including host, user, password, domain 
    and share. The full specification of the UNC string is:

                \\domain\user:password@host\share\path

      @param unc (str): the UNC path. If it does not contain password
        information, it will be prompted to the console
      @param subpath (str): an optional subpath to add at the end of the 
        UNC path
      @return (dict): the result data, separated by component
    """
    m = re.match( r"""\\\\
                      (?: (?: (?P<domain>[-.\w]+) \\ )?
                              (?P<user>\w+)
                              (?: : (?P<pass>\w+) )?
                       @ )?
                      (?P<host>[-.\w]+)
                      \\
                      (?P<share>[^\\]+)
                      (?: \\
                          (?P<path>.+) )?""", unc, re.X )
    if not m:
        raise InvalidArgumentError( 'can\'t understand SMB UNC: %' % unc )
    d = m.groupdict()
    if d['user'] is None:
        d['user'] = os.getlogin()
    if d['domain'] is None:
        d['domain'] = DOMAIN
    if d['pass'] is None:
        d['pass'] = getpass.getpass("Please insert password for SMB user '{domain}\\{user}' on {host}: ".format( **d ) )
    d['path'] = os.path.join(d['path'], subpath) if d['path'] else subpath
    #print d
    return d




# ---------------------------------------------------------------------


class SMBTransport( BaseWTransport ):
    """
    A full R/W transport connecting to a remote folder via a Windows
    share (SMB protocol), using the pysmb module
    **UNFINISHED WORK**
    (there are pending authentication problems against oriente.hi.inet)
    """
    def __init__( self, url, subrepo ):
        super(SMBTransport,self).__init__()
        d = parse_unc( url, subrepo )
        n = NetBIOS();  #r = n.queryName( d['host'] ); print r
        smb_name = n.queryIPForName( gethostbyname(d['host']) ); 
        #print "NAMES: ", smb_name
        if True:
            self.conn = mySMBConnection( d['user'], d['pass'], gethostname(), 
                                         smb_name[0], domain=d['domain'], 
                                         use_ntlm_v2 = False, 
                                         sign_options = smb.SMBConnection.SMBConnection.SIGN_WHEN_SUPPORTED,
                                         is_direct_tcp = False)
            r = self.conn.connect( gethostbyname(d['host']), 139 )
           #self.conn.close()
        else:
            self.conn = mySMBConnection( d['user'], d['pass'], gethostname(), 
                                         smb_name[0], domain=d['domain'], 
                                         use_ntlm_v2 = False, 
                                         sign_options = smb.SMBConnection.SMBConnection.SIGN_WHEN_SUPPORTED,
                                         is_direct_tcp = True)
            r = self.conn.connect( gethostbyname(d['host']), 445 )
        self.cdata = d

    def init_base( self ):
        """Ensure the base path for the repository exists"""
        pass

    def get( self, sourcename, dest ):
        path = os.path.join( self.cdata['path'], sourcename )
        self.conn.retrieveFile( self.cdata['share'], path, dest )

    def put( self, source, destname ):
        pass

    def delete( self, filename ):
        pass

    def rename( self, oldname, newname ):
        pass

    def otype( self, path ):
        """
        Given a path component, return 'F' for a file, 
        'D' for a directory, or None if the path does not exist
        """
        pass

    def folder_create( self, path ):
        """
        Make a folder in the repository, assuming all parent folders exist
        """
        pass

    def folder_list( self, path ):
        """
        Return the list of all components (files & folders) in a folder
        """
        pass


