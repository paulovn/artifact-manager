
import sys

# ---------------------------------------------------------------------


# SMB domain for authentication
DOMAIN = 'HI'

# Repository configuration: names of management files/dirs
BACKEND_VERSION = 3
OPTIONS = 'options'
INDEX = 'index'
REFS = 'refs'
BRANCHES = 'branches'
LOGS = 'logs'
OBJECTS = 'objects'
OPTIONS_SECTION = 'general'

# Default options
DEFAULT_OPTIONS = { 'version' : BACKEND_VERSION,
                    'git_ignored' : False,
                    'min_size' : 0,
                    'files' : (),
                    'extensions' : ('cache','dump','pkl',
                                    'mat',
                                    'rpm','deb',
                                    'mpg','mp3','mp4',
                                    'doc','docx','xls','xlsx','ppt','pptx',
                                    'ps','pdf','odt','ods','odp',
                                    'zip','tar','gz','bz2','rar') }

WHEREAMI = 'https://pdihub.hi.inet/paulo/artifact-manager'
README = """<html><body>
<p>
This folder contains a managed artifact repository, containing artifacts 
to deploy on top of a local folder (typically a git-managed working area, 
but not necessarily). Artifacts can be versioned, using the definition
of "artifact branches" as "sets of files that go together".
</p>
<p>
It is operated by means of the 'artifact-manager' script. Do not modify
files manually.
</p>
<p>
Note: though its structure has a certain resemblance with a Git
repository, it cannot be managed at all via Git commands.
</p>
<p>For further information, see:
<a href="{0}">{0}</a>
</p>
</body></html>""".format(WHEREAMI)


# ---------------------------------------------------------------------

class GenericError( Exception ):
    """An exception signaling a generic error in the processing"""
    def __init__( self, exception_type, msg=None, *args ):
        full_msg = exception_type + ': ' + msg if msg else exception_type
        super(GenericError,self).__init__(full_msg,*args)
        print self.args[0]
        sys.exit(1)

class TransportError( GenericError ):
    """An exception signaling a problem in the transport layer"""
    def __init__( self, msg=None, *args ):
        super(TransportError,self).__init__('Transport Error',msg,*args)

class InvalidArgumentError( GenericError ):
    """An exception signaling an invalid option"""
    def __init__( self, msg=None, *args ):
        super(InvalidArgumentError,self).__init__('Invalid Argument',msg,*args)


