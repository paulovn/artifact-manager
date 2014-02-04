import os
import shutil
import tempfile
import zipfile


# -------------------------------------------------------------------

def createTmpServer( repo=None ):
    tmpbase = tempfile.mkdtemp()
    if repo is not None:
        os.mkdir( os.path.join(tmpbase,repo) )
    return tmpbase


def deleteTmpServer( name ):
    shutil.rmtree( name )

# -------------------------------------------------------------------


def _populate_project( projectdir ):
    d1 = os.path.join(projectdir,'dir1')
    d2 = os.path.join(projectdir,'dir2')
    os.mkdir( d1 )
    os.mkdir( d2 )
    s = os.path.join(projectdir,'source.txt')
    with open(s,'w') as f:
        f.write('A simple file')
    with zipfile.ZipFile( os.path.join(d1,'artifact1.zip'), 'w' ) as z:
        z.write( s )
    

def createTmpProject( name=None ):
    tmpbase = tempfile.mkdtemp()
    _populate_project( tmpbase )
    return tmpbase

def deleteTmpProject( name ):
    shutil.rmtree( name )
