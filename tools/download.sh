#!/usr/bin/env bash
# download all theme files currently on shopify for each known environment.
# Must be run in the top level of the repo.
# Then, you can do somethig like rsync -nirc download/development/ ./ and see
# how it looks.

cat config.yml | grep '^[^ #]' | cut -f 1 -d : | while read environ; do
	dir="download/$environ"
	echo "$dir"
	mkdir -p "$dir"
	theme download -e $environ -d "$dir"
done
