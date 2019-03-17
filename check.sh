#!/usr/bin/env bash

# Javascript Lint
function check_javascript_all {
	find . -name '*.js' -o -name '*.js.liquid' -a ! -name 'js-instafeed.js' -exec jshint {} +
}

function check_liquid_all {
	export -f check_liquid_file
	find . -iname '*.liquid' -exec bash -c 'check_liquid_file "$@"' _ {} \;
}

# Wrapper for liquid-linter than strips out the unrecognized "-" characters
# shopify uses to control whitespace.
function check_liquid_file {
	liquid_in=$1
	liquid_tmp=$(mktemp --suffix=.liquid)
	sed 's/{%-/{%/g;s/-%}/%}/' "$liquid_in" > "$liquid_tmp"
	liquid-linter "$liquid_tmp" | sed "s:$liquid_tmp:$liquid_in:"
}

function check_main {
	check_javascript_all
	check_liquid_all
}
