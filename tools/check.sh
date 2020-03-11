#!/usr/bin/env bash

# Javascript Lint
function check_javascript_all {
	(
	set -o errexit -o pipefail
	# First, plain ol' javascript
	find . -name '*.js' -a ! -name '*.min.js' -exec jshint {} +
	# Separately handle liquid-templated-javascript with a kludgy bit of
	# sed to hide it from jshint
	find . -name '*.js.liquid' | while read fn; do
		jshint <(sed "s/{{.*}}/0/" "$fn") | sed -r "s:^/dev/fd/[0-9]+:$fn:"
	done
	)
}

# CSS Lint with stylelint
# This excludes liquid-templated CSS because I'm not sure how to get stylelint to
# handle it.
function check_css_all {
	stylelint assets/style*.css
}

# Liquid Lint
function check_liquid_all {
	stash=$(mktemp -d)
	lintout=$(
	set -o errexit -o pipefail
	# Wrapper for liquid-linter than strips out the unrecognized "-"
	# characters shopify uses to control whitespace.
	find . -iname '*.liquid' -exec rsync -rR {} $stash/ \;
	find "$stash" -type f -exec sed -i 's/{%-/{%/g;s/-%}/%}/' {} \;
	liquid-linter \
		--custom-tag layout \
		--custom-tag form \
		--custom-tag endform \
		--custom-tag paginate \
		--custom-tag endpaginate \
	       "$stash" |& sed "s:$stash:.:" | grep -v ': no issues found$'
	)
	if [[ $stash != "" ]]; then
		rm -rf "$stash"
	fi
	if [[ $lintout != "" ]]; then
		echo "$lintout"
		return 1
	fi
}

function check_main {
	check_javascript_all || retval=$?
	check_css_all || retval=$?
	check_liquid_all || retval=$?
	return $retval
}

if [[ ${FUNCNAME[0]} == main ]]; then
	check_main
fi
