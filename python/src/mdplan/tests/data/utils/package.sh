#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail
if [[ "${TRACE-0}" == "1" ]]; then
	set -o xtrace
fi

if [[ "${1-}" =~ ^-*h(elp)?$ ]]; then
	echo 'Usage: ./package.sh arg-one arg-two

Creates a package for the repo.
'
	exit
fi

main() {
	name=$1
	tar -czf $name.tar.gz $name
}

main "$@"
