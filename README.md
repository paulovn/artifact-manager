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

Available transports to connect to the remote repository are:

* HTTP for read-only operations (list, check, download)
* Local folder for upload operations (mount a remote disk locally to
  be able to upload to a remote repo)
* SMB (_in the works_) for upload operations


Repository specification
------------------------

A repository is defined on top of a transport layer (each transport
endpoint can contain a number of repositories) with a string. On top
of that, a branch is also an arbitrary string (usually with a path-like shape)

These parameters can also be automatically defined if the project tree
is a checked out Git repo. In this case Git is used to extract the
name of the artifact repository to use (will have the same name as the
git repo, minus the `.git` suffix) and the artifact branch (the
currently checked out branch). This selection can be overriden with
command line parameters.


In summmary, the parameters that can be defined needed for operation are

* Local project tree: use a positional argument; else the current
  working directory will be used
* Repository name: use the `--repo-name <name>` option; else it will
  be taken from Git info
* Branch name: use the `--branch <name>` option; else it will be taken from 
  Git info

To be able to fetch Git info, the `git` command-line executable will
be tried first; if not available the ".git" directory will be searched.



Execution options
-----------------

Options defining the behaviour (these are settable _per repository_,
and can also be overriden at runtime):

* --extensions
* --min-size

Other options:

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
