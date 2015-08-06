docdirs = $(wildcard *-doc)

all: $(docdirs)
	for dir in $(docdirs); do \
		(set -eu; cd "$$dir" && \
		../format-as-pdf "$$dir.pdf" \
		$$(find -name '*.yarn' -o -name '*.mdwn' -o -name '*.dia' \
                        -o -name '*.dot' | sort)); \
	done
