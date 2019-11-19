#! python3
# coding=utf-8

# gen-argparse.py
# copyright 2019 Brian Fitzgerald

# Read a command-line specification file and create an argparse parser for it
# (https://docs.python.org/3/library/argparse.html)

import os
import sys
if sys.version_info < (3,5):
    raise Exception("Requires Python 3.5 or greater")

def main():
    if len(sys.argv) < 2:
        print("No specfile supplied\n")
        return
    specfile = sys.argv[1]

    specs = readspecs(specfile)
    print("We have %d commands" % len(specs))
    with open("argparser.py", "wt", encoding='utf-8') as f:
        genCommands(f, specs)

# -----------------------------------------------------------------------------------------------

def genCommands(f, specs):

    # translate table to fix up strings with quotes in them
    fixquot = str.maketrans({"'": r"\'"})

    # Generate the top-level parser with the calls to the subparsers
    callsub = ""
    for spec in specs:
        (cmdid, cmdname, usage, opts) = spec
        # print("Generating code for %s" % cmdname)

        subparser = "    subparser_%s(subparsers)\n" % cmdid
        callsub += subparser

    # Now generate the parsers themselves
    subs = ""
    for spec in specs:
        (cmdid, cmdname, usage, opts) = spec
        # print("Generating code for %s" % cmdname)

        subs += "\n# ---------------------------------\n\n"
        subs += "def subparser_%s(subparsers):\n" % cmdid
        # subs += "    pass\n"

        # Build usage string
        usagetext = ""
        firstline = True
        for L in usage[1:]:
            if not firstline:
                usagetext += "\\\n"
            firstline = False
            usagetext += L

            # Escape quotes in help text
            usagetext = usagetext.translate(fixquot)

        subs += "    subparser = subparsers.add_parser('{cmdid}', usage='{usage}')\n".format(cmdid=cmdid, usage=usagetext)

        # Build options
        for opt in opts:
            if opt[0] == "groupline":
                subs += "    # groupline functionality needs a custom formatter_class\n"
            elif opt[0] == "textline":
                subs += "    # textline functionality needs a custom formatter_class\n"
                pass
            else:
                (optname, shortname, longname, argument, hidden, optional, helptext, argtype, numopt) = opt[1:]

                # We can't handle numopt yet
                if numopt:
                    subs += "    # %s can't handle numopt yet\n" % optname
                    continue

                # An option with just a shortname of -h can't be parsed at the moment
                if shortname == "h" and len(longname) == 0:
                    subs += "    # %s tried to define -h which conflicts with help\n" % cmdname
                    continue

                optlist = ""
                if len(longname) > 0:
                    optlist = "'--" + longname + "'"
                if len(shortname) > 0:
                    if shortname == "h":
                        subs += "    # %s tried to add -h which conflicts with help\n" % longname
                    else:
                        if len(optlist) > 0:
                            optlist += ", "
                        optlist += "'-" + shortname + "'"

                actiontext = "**UNHANDLED**"
                if argtype == "bool":
                    actiontext = ", action='store_true'"
                elif argtype == "string":
                    actiontext = ""
                elif argtype == "int":
                    actiontext = ", type=int"

                # add warning if hidden
                if hidden:
                    subs += "    # %s should be marked hidden, but that needs a custom formatter_class\n" % longname

                # Escape quotes in help text
                helptext = helptext.translate(fixquot)

                subs += "    subparser.add_argument({options}, dest='{dest}'{action}, help='{help}')\n".format(
                    options=optlist, dest=optname, action=actiontext, help=helptext)

    # Output everything
    callsub = callsub.rstrip()
    subs = subs.rstrip()
    print(parserTemplate.format(insertsubparsers=callsub, subparsers=subs), file=f)

parserTemplate = """# parser

import argparse

def main():
    parser = create_parser()
    args = parser.parse_args()
    # print(args)

def create_parser():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

{insertsubparsers}

    return parser
{subparsers}

if __name__ == '__main__':
    main()
"""

# -----------------------------------------------------------------------------------------------

# Read the command-spec file into a data structure
# A file looks like this:
#    command add
#        usage
#            "usage: git add [<options>] [--] <pathspec>..."
#        option dryRun
#            shortname: n
def readspecs(specfile):
    cmds = []
    with open(specfile, "rt", encoding='utf-8') as f:
        n = 1
        line = f.readline().rstrip()
        # print("%d: %s" % (n, line))
        while line:

            # We must be at a "command xxx" line. Parse the command name, and strip
            # a trailing " cmd" text annotation to just get the text of the command,
            # since that's what argparse is going to want
            if not line.startswith("command "):
                raise Exception("expected 'command' in line %d: got '%s'" % (n, line))
            cmdid = line[8:]
            cmdname = cmdid
            textoffset = cmdid.find(" \"")
            if textoffset != -1:
                cmdname = cmdid[textoffset+2:-1]
                cmdid = cmdid[:textoffset]

            # Parse usage and options
            usage, line, n = readcmdusage(f, n)
            opts, line, n = readcmdoptions(f, line, n)

            # Put into a data structure
            cmd = [cmdid, cmdname, usage, opts]
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
