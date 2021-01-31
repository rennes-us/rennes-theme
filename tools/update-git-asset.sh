#!/usr/bin/env bash
(
echo "Last commit: $(date -Iseconds)"
echo "Last tag:    $(git describe --tags --long)"
echo "Last title:  $(git log -n 1 --pretty=format:%s)"
) > assets/version.txt
