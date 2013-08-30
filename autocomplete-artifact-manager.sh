#!/bin/bash

# Provide simple autocompletion for the 'artifact-manager' command
__artifact_manager()
{
    local cur prev opts
    COMPREPLY=()
    if [[ "${COMP_CWORD}" == "1" ]]; then
	commands="list diff download get upload branches getoptions setoptions rename-branch"
        COMPREPLY=( $(compgen -W "${commands}" -- ${cur}) )
        return 0
    fi
}
complete -F __artifact_manager artifact-manager
