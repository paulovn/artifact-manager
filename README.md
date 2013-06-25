artifact-manager
================

A Python script to manage a repository of project artifacts, possibly
versioned.  Each repository contains a list of "branches"; each branch
is defined by a list of artifacts (which may vary or repeat
individually from branch to branch). Location info for each artifact
in the project tree is preserved.


It accepts the following operations:

 * __list__  List the artifacts stored in a remote repo for a given branch

 * __check__ Compare the artifacts in the local tree with the remote repo

 * __download__  Fetch artifacts for the current branch from the repo.
     Only new & modified artifacts will be downloaded. They will be
     left in their defined places in the project tree.

 * __upload__  Upload all local artifacts to the repo, defining the set for
       the current branch. Only new/modified files will be uploaded

 * __purge__	  *future op*

 * __setoptions__ *future op*



Transports
----------

* HTTP for read-only operations (list, check, download)
* Local folder for upload operations (mount a remote disk locally)
* SMB (in the works) for upload operations


Argument specification
----------------------

A repository is defined on top of a transport layer (each transport
endpoint can contain a number of repositories) with a string. On top
of that, a branch is also an arbitrary string (usually with a path-like shape)

The parameter needed for operation are

* Repository name
* Branch name
* Local project tree


Configuration options
---------------------

* --extensions
* --min-size


Other options
-------------

* --verbose <n>
* --dry-run
* --overwrite


Requirements
------------

* Python 2.6 or above

* The following non-core Python modules (all available as
  standard Python modules in PyPI)
   - [httplib2](https://pypi.python.org/pypi/httplib2/0.8)
   - [pysmb](https://pypi.python.org/pypi/pysmb/1.1.5) (only to use SMB
     transports for artifact upload)

* A working git command, only for automatic selection of repository
  name and branch name (this requirement can be sidestepped by using
  the `--repo-name` and `--branch` command-line arguments)