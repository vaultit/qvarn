#!/bin/bash

set -eu

cd "$(dirname "$0")"

appendix()
{
    local x
    echo
    echo '# Complete listings'
    for x in *.py views/*.tpl
    do
        echo
        echo "## $x"
        echo
        echo ~~~~~~~~~~~~~~~~~~~~~~~~
        nl -ba "$x"
        echo ~~~~~~~~~~~~~~~~~~~~~~~~
    done
}


appendix > zzzz-appendix.mdwn
