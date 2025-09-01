#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail
if [[ "${TRACE-0}" == "1" ]]; then
	set -o xtrace
fi

if [[ "${1-}" =~ ^-*h(elp)?$ ]]; then
	echo 'Usage: ./unpackage.sh repo_folder_name

Expands an example data repo for use in testing.
'
	exit
fi

main() {
	name=$1
	tar -xzf $name.tar.gz
}

main "$@"
