# Python command-line parsing

## argparse

`gen-argparse.py` turns a command-line spec into code that uses the Python
standard library [`argparse`](https://docs.python.org/3/library/argparse.html)

Generate:

```
$ gen-argparse.py ../spec/git-command-specs.txt
```

which, by default, writes to `argparser.py` in the current directory.

Time it (with [Hyperfine](https://github.com/sharkdp/hyperfine)):

```
$ hyperfine argparser.py
Benchmark #1: argparser.py
  Time (mean ± σ):     198.5 ms ±   5.0 ms    [User: 10.1 ms, System: 52.2 ms]
  Range (min … max):   193.2 ms … 213.4 ms    14 runs
```

This is with zero command-line arguments, but adding command-line arguments doesn't affect
the timing much.

```
$ hyperfine "argparser.py add --dry-run -v --interactive --edit"
Benchmark #1: argparser.py add --dry-run -v --interactive --edit
  Time (mean ± σ):     198.8 ms ±   1.9 ms    [User: 16.4 ms, System: 47.7 ms]
  Range (min … max):   196.2 ms … 202.4 ms    14 runs
```

As expected, the argparse library imposes a pretty hefty startup time
cost, since the command-line parser is built from, in this case, over 2000 calls to argparse
library functions.

This is probably going to be the slowest of all the command-line parsing libraries, although
it will be interesting to see what happens with the Go standard library [`flag`](https://golang.org/pkg/flag/)
or things built on top of it like [`spf13/pflag`](https://github.com/spf13/pflag).

### non-naive approach

Although it would be more complex, if you really want to do complex command-lines in Python,
some restructuring is in order. Only the top command-line is created at startup, with the
base options, a positional argument for the verb, and then using the partial parsing to
pass the remaining unparsed arguments to a specific sub-parser that you create.

Fortunately, if you follow the code-generation approach, experimenting with things like
this just means writing a new generator.

TBD.
