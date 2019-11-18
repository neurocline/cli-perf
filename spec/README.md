# Command-line specifications

`git-command-specs.txt` is the specification for the Git command-line, as of Git 2.20.1.

# Command-line spec format

The current spec format is simple and uses an ad-hoc file format. Call this version 0, because
it's very likely to change.

Todo:

- use YAML or TOML instead of ad-hoc?

```
command <cmdid> "<cmdname>"
    usage
        "<usage string>"
    option <optid>
        shortname: <shortname>
        longname: <longname>
        argument: <argument>
        hidden
        groupline
        type: <type>
        help: "<help string>"

```

The `<cmdid>` field is in identifier form, suitable for use as an identifier in most languages.
The `<cmdname>` field is the actual text used in the command-line.

Strings can be multi-line, and linebreaks are preserved; e.g. this usage string would be
displayed as multiple lines, with the indentation shown:

```
    usage
        "usage: git am [<options>] [(<mbox> | <Maildir>)...]"
        "   or: git am [<options>] (--continue | --skip | --abort)"
```

Options:

The possible option parameters in order of how they appear in the spec are:

- optname, shortname, longname, argument, hidden, optional, helptext, type, numopt

Argument can be used as a pattern to runtime filtering on values. For example, a string that can only
be "-x" or "+x" is written like this:

```
    option chmod
        longname: chmod
        argument: (+|-)x
        type: string
        help: "override the executable bit of the listed files"
```

Typically, argument is just a symbolic name indicating some kind of type to the user:

```
    option output
        shortname: o
        longname: output
        argument: <file>
        type: string
        help: "write the archive to this file"
```

The `hidden` parameter indicates that this option is parsed, but not shown in help to the user
(for Git, `--help-all` will show hidden options).

The `groupline` parameter is cosmetic, and will cause a blank line to appear in the help output;
this is used to group options into visual sets for complex commands. If used, this is expected
to be the only argument for that option.

The `type` parameter is a strong type for the option value; the current set includes

- `bool`
- `string`
- `int`

As seen above, enum-like types are emulated with `string` and a pattern in `argument`.

The `numopt` parameter indicates that the option is written as `-<NUM>`, meaning any
number can be supplied. In this case, there is no `shortname` or `longname`, and in the
current implementation, it's listed as `type: bool` (these kinds of options have no
associated "value"). for Git, we see this in one place:

```
command grep "grep"
    usage
        "usage: git grep [<options>] [-e] <pattern> [<rev>...] [[--] <path>...]"
...
    option num
        numopt
        type: bool
        help: "shortcut for -C NUM"
```
