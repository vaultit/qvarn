#!/bin/bash

set -eu

cd "$(dirname "$0")"

source()
{
    cat authorization_code_flow_webapp.md
    echo
    echo '# Appendix: full listing'
    echo
    echo ~~~~~~~~~~~~~~~~~~~~~~~~
    nl -ba authorization_code_flow_webapp.py
    echo ~~~~~~~~~~~~~~~~~~~~~~~~
}

pandoc \
    --from=markdown+header_attributes+auto_identifiers \
    --chapters \
    --number-sections \
    --toc --toc-depth=2 \
    --latex-engine=xelatex \
    -V geometry:a4paper \
    -V documentclass=report \
    -V fontsize:12pt \
    -V mainfont:"Verdana" \
    -V sansfont:"Liberation Sans" \
    -V monofont:"Liberation Mono" \
    -V geometry:"top=2cm, bottom=2.5cm, left=2cm, right=1cm" \
    -o authorization_code_flow_webapp.pdf \
    <(source) \
    "$@"
