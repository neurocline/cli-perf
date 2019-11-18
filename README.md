# cli-perf

Test performance of command-line parsing libraries in multiple languages.

We do this by using large command-line interfaces, written in a generalized spec form,
and then using code generators to turn that into code for a given command-line parsing
library. Then we measure: build-time (where relevant), startup time, and then time
parsing a command-line.

This is a multi-library and multi-language approach. Any library in any language could be
tested in this fashion. The expectation is that the information from this is used to guide
selection and development of command-line parsing libraries.

## Repo structure

This is organized by language, for lack of a better way to do it. Some of the tools are
not yet written in all languages.
