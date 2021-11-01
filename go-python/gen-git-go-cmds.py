#! python3
# coding=utf-8

import os
import sys
if sys.version_info < (3,5):
    raise Exception("Requires Python 3.5 or greater")

def main():
    specs = readspecs()
    print("We have %d commands" % len(specs))
    genCommands(specs)

# Generate output from specs
def genCommands(specs):
    if not os.path.exists("builtin"):
        os.mkdir("builtin")

    for spec in specs:
        (cmdname, usage, opts) = spec
        print("Generating code for %s" % cmdname)

        # We need this for do<command>
        cmdnameUpper = cmdname[0].upper() + cmdname[1:]

        # Build usage as a single string
        usagetext = "var usage []string = []string{"
        firstline = True
        for L in usage[1:]:
            if not firstline:
                usagetext = usagetext + ",\n\t\t\t\t\t\t\t\t  "
            usagetext = usagetext + "\"" + L + "\""
            firstline = False
        usagetext = usagetext + "}"

        # Build vars and options
        varstext = ""
        optionstext = ""
        for opt in opts:
            if opt[0] == "groupline":
                optionstext = optionstext + "\t\t{ \"\",  \"\", nil, \"\", \"\" },\n"
            elif opt[0] == "textline":
                # We can't handle this yet, drop it
                #raise Exception("didn't handle textline yet")
                pass
            else:
                (optname, shortname, longname, argument, hidden, optional, helptext, argtype, numopt) = opt[1:]
                goargtype = "unknown"
                if argtype == "bool":
                    goargtype = "bool"
                elif argtype == "string":
                    goargtype = "string"
                elif argtype == "int":
                    goargtype = "int"
                varstext = varstext + "\t" + optname + " " + goargtype + "\n"

                optline = "unknown"
                if argtype == "bool":
                    optline = "\t\t{ \"%s\", \"%s\", newBoolValue(&g.%s, false), \"%s\", \"%s\" },\n" % (
                                shortname, longname, optname, argument, helptext)
                elif argtype == "string":
                    optline = "\t\t{ \"%s\", \"%s\", newStringValue(&g.%s, \"\"), \"%s\", \"%s\" },\n" % (
                                shortname, longname, optname, argument, helptext)
                elif argtype == "int":
                    optline = "\t\t{ \"%s\", \"%s\", newIntValue(&g.%s, 0), \"%s\", \"%s\" },\n" % (
                                shortname, longname, optname, argument, helptext)
                else:
                    raise Exception(opt)

                optionstext = optionstext + optline

        varstext = varstext.rstrip()
        optionstext = optionstext.rstrip()

        filename = "builtin/%s.go" % cmdname
        with open(filename, "wt", encoding='utf-8') as f:
            print(fileTemplate.format(cmdname=cmdname, cmdnameupper=cmdnameUpper,
                usage=usagetext, vars=varstext, options=optionstext), file=f)

fileTemplate = """// {cmdname}.go

package main

import (
\t"fmt"
)

type {cmdname}Vars struct {{
{vars}
}}

func do{cmdnameupper}(args []string, opts globalOptions) int {{
\tvar g {cmdname}Vars
\t{usage}
\tvar options []Option = []Option{{
{options}
\t}}

\tvar parameters []string
\tvar err error
\tif parameters, err = parseOptions(args, options, usage); err != nil {{
\t\tif err.Error() == "EXIT" {{
\t\t\treturn 0
\t\t}}
\t\tfmt.Printf("parseOptions returned an error: %s""" + "\\n\"" + """, err)
\t\treturn 1
\t}}

\tfmt.Printf("%#v parameters=%s""" + "\\n\\n\"" + """, g, parameters)
\treturn 0
}}
"""

# Read the command-spec file into a data structure
# A file looks like this:
#    command add
#        usage
#            "usage: git add [<options>] [--] <pathspec>..."
#        option dryRun
#            shortname: n
def readspecs():
    cmds = []
    with open("git-command-specs.txt", "rt", encoding='utf-8') as f:
        n = 1
        line = f.readline().rstrip()
        # print("%d: %s" % (n, line))
        while line:

            # We must be at a "command xxx" line. Parse the command name, and strip
            # a trailing " cmd" text annotation to just get the ID form of the command
            if not line.startswith("command "):
                raise Exception("expected 'command' in line %d: got '%s'" % (n, line))
            cmdname = line[8:]
            textoffset = cmdname.find(" \"")
            if textoffset != -1:
                cmdname = cmdname[:textoffset]

            # Parse usage and options
            usage, line, n = readcmdusage(f, n)
            opts, line, n = readcmdoptions(f, line, n)

            # Put into a data structure
            cmd = [cmdname, usage, opts]
            cmds.append(cmd)

    return cmds

# Read the usage section
def readcmdusage(f, n):
    # We expect a usage header
    line = f.readline().rstrip()
    if line.lstrip() != "usage":
        raise Exception("expected 'usage' in line %d: got '%s'" % (n, line))

    # Read usage until we see the first option, or the next command
    # (if there are no options)
    usage = []
    while line:
        n = n + 1
        # print("%d: %s" % (n, line))
        line = line.lstrip()

        if line.startswith("option") or line.startswith("command "):
            break
        usage.append(line[1:-1])

        line = f.readline().rstrip()

    return usage, line, n

# Read the option sections
def readcmdoptions(f, line, n):
    opts = []

    # Keep reading until we see command or end of file
    while line:
        if line.startswith("command "):
            break
        if not line.startswith("option"):
            raise Exception("expected 'option' in line %d: got '%s'" % (n, line))

        # Read an option until we see the next option or command
        optname = ""
        if len(line) > 7:
            optname = line[7:]
        shortname = ""
        longname = ""
        argument = ""
        hidden = False
        optional = False
        helptext = ""
        argtype = ""
        numopt = False
        textline = ""
        groupline = False

        # Read the next line to prime the pump.
        line = f.readline().rstrip()

        while line:
            n = n + 1
            # print("%d: %s" % (n, line))
            line = line.lstrip()

            if line.startswith("shortname: "):
                shortname = line[11:]
            elif line.startswith("longname: "):
                longname = line[10:]
            elif line.startswith("argument: "):
                argument = line[10:]
            elif line == "hidden":
                hidden = True
            elif line == "optional":
                optional = True
            elif line.startswith("help: "):
                helptext = line[7:-1]
            elif line.startswith("type: "):
                argtype = line[6:]
            elif line == "numopt":
                numopt = True
            elif line == "groupline":
                groupline = True
            elif line.startswith("textline: "):
                textline = line[10:]
            elif line.startswith("option") or line.startswith("command "):
                break
            else:
                raise Exception("unknown", line, opt)

            line = f.readline().rstrip()

        # Now that we have the pieces from an option, put it together
        opt = []
        if groupline:
            opt = [ "groupline" ]
        elif textline != "":
            opt = [ "textline", textline ]
        else:
            opt = [ "option", optname, shortname, longname, argument, hidden, optional, helptext, argtype, numopt ]

        opts.append(opt)

    return opts, line, n

# -----------------------------------------------------------------------------------------------

# This is just so that we can write code in what seems reasonable rather than
# in the order Python execution needs it.
if __name__ == '__main__':
    main()
