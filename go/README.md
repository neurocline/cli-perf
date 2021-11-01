# Go command-line parsing

## flag

It's not possible to do subcommands with the stock [flag](https://golang.org/pkg/flag/). Well,
I'm pretty sure it's not.

OK, I was wrong, but the documentation is, shall we say, terse. Or, rather, a documentation
style which is to tied to functions and types doesn't have a good place to describe why and
how.

```
$ go run gen-flag.go ../spec/git-command-specs.txt
```

The approach is to generate all the commands at once into flagsets, each of which handles
one level of command-parsing. This is done in individual functions, to minimize runtime;
there's no need to have a command handler for `git add`, for example, if the user typed
`git update`.

## spf13/pflag

`gen-pflag.go` turns a command-line spec into code that uses the
[spf13/pflag](https://github.com/spf13/pflag) library (originally written by Alex Ogier,
enhanced by Steve Francia).

Generate:

```
$ go run gen-pflag.go ../spec/git-command-specs.txt
```
