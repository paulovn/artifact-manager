artifact-manager
================

A Python script to manage a repository of project artifacts, possibly
versioned.  Each repository contains a list of "branches"; each branch
is defined by a list of artifacts (which may vary or repeat individually 
from branch to branch). Location info for each artifact in the project 
tree is preserved.

It has been designed to play nicely with a project hosted in a PDIHub
Git repository (i.e. it manages the files that cannot go into PDIHub
since they are binary artifacts), but can also be used independently. 

Note also that the concept of "branch", while it maps well to Git
branches, is not actually tied to them. A branch is actually no more
than a name (a string) that refers to a set of objects (a list of
artifacts), and can refer to anything in addition to an "actual" Git
branch.

An "artifact" in this context is a file in the project tree that
matches the selection restrictions (basically file extension and file
size).  A hash is computed for each artifact, so that if the file contents 
changes it will be detected as a new object event if its name and place 
remains the same (for the server they _are_ two different objects, and 
there is no relationship between them). Objects retain information about 
their name, path in the project tree and modification time.


It accepts the following operations:

 * __list__  List the artifacts stored in a remote repo for a given branch

 * __diff__ Compare the artifacts in the local tree with the branch in the 
     remote repo, or compare two branches in the remote repo

 * __branches__ List available branches in the repo in the remote server

 * __download__  Fetch the artifacts for the current branch from the repo.
     Only new & modified artifacts will be downloaded. They will be
     left in their defined places in the project tree.

 * __get__ Download one specific artifact file from one specific branch

 * __upload__  Upload all local artifacts to the repo, defining the set for
     the current branch. Only new/modified files will be uploaded

 * __getoptions__ Show the options currently defined (the ones fetched from
     the server, modified by any command-line arguments)

 * __setoptions__ Take the currently defined options (the ones fetched from
     the server, modified by any command-line arguments) and store them
     as repository options

 * __rename-branch__ Change the name of a branch in the repo

 * __remove-branch__ *future op*

 * __purge__	  *future op*



Intended PDIHub workflow
------------------------

To manage the artifacts associated to a PDIHub project, the envisioned
steps are as follows:

* To download artifacts, after the Git project has been cloned
  into a local repo, and the desired branch has been checked out, just
  execute `artifact-manager download` over the base directory of the
  project. The artifacts corresponding to that branch of the project
  will then be downloaded (over HTTP).

* Whenever the project switches to another branch, executing again
  `artifact-manager download --delete-local` will connect to the
  artifact repository and update the artifacts in the local directory
  to match the new branch (the script is smart enough to download only
  the new or changed files, which comes handy if those files are large).

* For artifact upload, the command to be executed when positioned in the 
  local folder is `artifact-manager --server-url <dir> upload` [1]. It will 
  collect all local artifacts, upload the ones not yet in the server,
  and label the set in the server with the current checked-out branch [2]

* If the local project changes to another branch, repeat the upload process
  and the local artifacts will be registered (and uploaded, if necessary) as 
  belonging to the new branch

* Whenever there is variation in the local artifacts, issuing the command  
  `artifact-manager --server-url <dir> upload --overwrite` will keep 
  the remote repository in sync with the local files. Note however that 
  the previous configuration for that branch will be lost: the server 
  keeps *only one version* of an artifact snapshot per branch [3].


On each of these operations the option `--dry-run` can be used to test
what the script would do without actually doing it.


[1] Currently the only working R/W transport is a local folder, so in
order for this to work, the remote server must be locally mounted as a
network disk (a native SMB transport layer is in the works)

[2] The first time this command is executed on a project, it will create
the artifact repository for that project in the repository server.

[3] The only thing that gets overwritten is the _definition_ of the
set of files covered by the branch. The files themselves do not get
overwritten; if the same file (with the same path) has changed, it is
uploaded as a new object, but the previous one is preserved (since it
may still be "alive" in another branch). The future `purge` operation
will clean the repository from orphaned objects (files no longer in
any branch)



Transports
----------

Available transports to connect to the remote repository are:

* HTTP for read-only operations (list, check, branches, download)
* Local folder for upload operations (to be able to upload to a remote repo, mount it locally as a network disk)
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

In summmary, the parameters needed for operation that can be defined are

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

Options modifying the detection of artifact files are:

* `--extensions` : a comma-separated list of the file extensions (with or
  without a leading period) that will be collected as artifacts. Note that if 
  the file name contains several dots, only the rightmost dot-extension will 
  be considered.
* `--min-size`: the minimum size of an artifact file to be included in
  the list (0 for files of any size)
* `--files`: files to be explicitly included as artifacts, if they exist,
  regardless of size. This is a multi-argument option: include as many files
  as needed, separated by spaces. Note that the option must *not* be immediately
  followed by any positional arguments (such as the operation, or the local 
  folder), or they will be taken as file names. It accepts shell-like globbing,
  with the `*`, `?` and `[charset]` metacharacters.
* `--git-ignored`: select as artifacts all files that will be ignored
  by git, as defined in the checked out repo. This option needs a
  working command-line git.

The script accepts both (`--extensions` + `--min-size`) and `--files` at the 
same time, so they can be freely combined. `--git-ignored`, however, is an 
exclusive argument: when used, the script ignores `--extensions`, `--min-size` 
and `--files`.

These are settable _per repository_: when the remote repository is
created (upon first artifact upload) the _extensions/min-size/files/git-ignored_
definitions at that time are stored as repository configuration, and
used henceforth. It can be overriden at runtime for a given execution, or 
re-stored with the __setoptions__ operation.

Other command-line options are:

* `--verbose <n>`: level of verbosity (default is 1)
* `--dry-run` do not actually modify either local or remote files
* `--overwrite`: when uploading, if the branch already exists overwrite its
  definition. Without this option the upload operation will fails.
* `--delete-local`: when downloading, delete detected local artifacts
  that do not appear in the object list for the current branch. Otherwise they
  are left alone.
* `--other-branch`: when comparing artifacts, compare the current branch against
   another branch in the remote repo, instead of against the local files
* `--name`: name of the artifact to download, for singe-file __get__ operations
* `--outname`: for __get__ operations, name to give to the downloaded file (if 
  not specified, the same name & path as recorded in the branch will be used)
* `--subdir <dir>`: for __diff__ and __download__ operations, work only with 
  artifacts belonging to a subdirectory of the project (for this to work well, 
  the defined local project dir must be that subdirectory, otherwise artifacts
  will not be downloaded to its correct place)

Requirements
------------

It needs either

* Python 2.7, or

* Python 2.6 + the [argparse](https://pypi.python.org/pypi/argparse)
  Python package (which is part of the Python Standard Library in 2.7)

and, optionally,

* The [pysmb](https://pypi.python.org/pypi/pysmb/1.1.5) Python module,
  only to use SMB transport for artifact upload
