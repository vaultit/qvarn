docdirs = $(wildcard *-doc)

all: $(docdirs)
	for dir in $(docdirs); do \
		(set -eu; cd "$$dir" && \
                if [ -e format.sh ]; then ./format.sh; fi; \
		../format-as-pdf "$$dir.pdf" \
		$$(find -name '*.yarn' -o -name '*.mdwn' -o -name '*.dia' \
                        -o -name '*.dot' | sort)); \
	done
