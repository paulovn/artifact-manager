#!/bin/bash

# Provide Bash simple autocompletion for the 'artifact-manager' command

__artifact_manager()
{
    local cur opts add
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    if [[ "${COMP_CWORD}" == "1" ]]; then
	# command completion
	opts="list diff download get upload branches getoptions setoptions rename-branch"
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
        return 0
    elif [[ "${cur:0:2}" = '--' ]]; then
	# long option completion
	if   test "${COMP_WORDS[1]}" = "upload";   then add=" overwrite"
	elif test "${COMP_WORDS[1]}" = "download"; then add=" delete-local"
	elif test "${COMP_WORDS[1]}" = "diff";     then add=" show-all"
	elif test "${COMP_WORDS[1]}" = "get";      then add=" outname"
	fi
	opts="verbose dry-run server-url repo-name branch subdir project-dir extensions files min-size git-ignored$add"
        COMPREPLY=( $(compgen -P "--" -W "${opts}" -- "${cur:2}") )
	return 0
    elif [[ -n "${cur}" ]]; then
	# else, do filename completion, if we have typed something
        COMPREPLY=( $(compgen -A file -- "${cur}") )
	return 0
    fi
	
}

complete -F __artifact_manager -o filenames artifact-manager
