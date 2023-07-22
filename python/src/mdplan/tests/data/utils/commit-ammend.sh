#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail
if [[ "${TRACE-0}" == "1" ]]; then
	set -o xtrace
fi

if [[ "${1-}" =~ ^-*h(elp)?$ ]]; then
	echo 'Usage: ./commit-ammend.sh isodate [author]

This will ammend the last commit using the given date and optional author.

'
	exit
fi

main() {
	date=$1
	author=${2:-"Martin L King <martin@mlk.org>"}
	GIT_COMMITTER_DATE="$date" git commit --date="$date" --author="$author" --amend
}

main "$@"
