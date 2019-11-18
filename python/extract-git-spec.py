#! python3
# coding=utf-8

# extract-git-spec.py
# copyright 2019 Brian Fitzgerald

# This program extracts the spec for the Git command-line from a git executable, so that
# we can always have an up-to-date Git spec. This works because the Git command-line help is
# nearly complete (it's lacking in a few areas). This was written as part of a yet-unpublished
# project, and copied here for convenience.

# todo: the list of Git commands was put together by inspection; use git help --all to
# check for new commands.

import codecs
import os
import re
import subprocess
import sys
if sys.version_info < (3,5):
    raise Exception("Requires Python 3.5 or greater")

debuglogs = False # enable/disable extra debug logs
writeraw = False # enable/disable rawhelp.txt log
writeparse = False # enable/disable parsehelp.txt
writetest = False # enable/disable testhelp.txt log (and testing)
writespecs = True # write specs to git-command-specs.txt
writemarkdown = False # write specs to git-command-specs.md
writehtml = False # write specs to git-command-specs.html

def main():
    for f in ("rawhelp.txt", "parsehelp.txt", "usageonly.txt", "usagenonblank.txt", "testhelp.txt",
              "git-command-specs.txt", "git-command-specs.md", "git-command-specs.html"):
        if os.path.exists(f):
            os.remove(f)

    # getRawUsageOnly()
    getRawHelp()

git_commands = [
    "add", "am", "annotate", "apply", "archimport", "archive", "bisect",
    "blame", "branch", "bundle", "cat-file", "check-attr", "check-ignore",
    "check-mailmap", "checkout", "checkout-index", "check-ref-format",
    "cherry", "cherry-pick", "citool", "clean", "clone", "column", "commit",
    "commit-graph", "commit-graph read", "commit-graph verify", "commit-graph write",
    "commit-tree", "config", "count-objects", "credential",
    "credential-cache", "credential-store", "cvsexportcommit", "cvsimport",
    "cvsserver", "daemon", "describe", "diff", "diff-files", "diff-index",
    "diff-tree", "difftool", "fast-export", "fast-import", "fetch",
    "fetch-pack", "filter-branch", "fmt-merge-msg", "for-each-ref",
    "format-patch", "fsck", "gc", "get-tar-commit-id", "grep", "gui",
    "hash-object", "help", "http-backend", "http-fetch", "http-push",
    "imap-send", "index-pack", "init", "instaweb", "interpret-trailers",
    "log", "ls-files", "ls-remote", "ls-tree", "mailinfo", "mailsplit",
    "merge", "merge-base", "merge-file", "merge-index", "merge-one-file",
    "mergetool", "merge-tree", "mktag", "mktree", "mv", "name-rev",
    "notes", "notes add", "notes copy", "notes append", "notes edit", "notes show",
    "notes merge", "notes remove", "notes prune", "notes get-ref",
    "p4", "pack-objects", "pack-redundant", "pack-refs", "parse-remote",
    "patch-id", "prune", "prune-packed", "pull", "push", "quiltimport",
    "read-tree", "rebase", "receive-pack",
    "reflog", "reflog show", "reflog expire", "reflog delete", "reflog exists",
    "remote", "remote add", "remote rename", "remote set-head", "remote show", "remote prune",
    "remote update", "remote set-branches", "remote get-url", "remote set-url",
    "repack", "replace", "request-pull", "rerere", "reset", "revert", "rev-list",
    "rev-parse", "rm", "send-email", "send-pack", "shell", "shortlog",
    "show", "show-branch", "show-index", "show-ref", "sh-i18n", "sh-setup",
    "stash", "stage", "status", "stripspace", "submodule", "svn",
    "symbolic-ref", "tag", "unpack-file", "unpack-objects", "update-index",
    "update-ref", "update-server-info", "upload-archive", "upload-pack",
    "var", "verify-commit", "verify-pack", "verify-tag", "whatchanged",
    "worktree", "write-tree",
]

git_commands_no_help_all = {
    "bisect", "commit-tree", "credential", "cvsexportcommit", "cvsimport",
    "diff", "fast-import", "filter-branch", "http-push", "mailsplit",
    "reflog", "rev-parse",
    "send-email", "stash", "svn", "unpack-file", "upload-archive",
}

git_commands_not_command = {
    "archimport", "citool", "credential-cache", "cvsserver", "gui",
    "http-backend", "p4", "parse-remote", "shell", "sh-i18n", "sh-setup",
}

git_commands_adhoc_help = {
    "diff-files", "diff-index", "diff-tree", "rev-list", "send-email", "svn",
}

git_commands_usage_only = []

def getRawUsageOnly():
    rawhelp = "rawhelp.txt" if writeraw else os.devnull
    with open(rawhelp, "at", encoding='utf-8') as f:
        print("================================================", file=f)
        print("Usage-only commands", file=f)
        print("================================================", file=f)
        print("", file=f)
    for cmd in git_commands_usage_only:
        print(cmd)
        rawUsage = run_git_usage(cmd)
        print(rawUsage)

def getRawHelp():
    rawhelp = "rawhelp.txt" if writeraw else os.devnull
    with open(rawhelp, "at", encoding='utf-8') as f:
        print("", file=f)
        print("================================================", file=f)
        print("Commands with internal help", file=f)
        print("================================================", file=f)
        print("", file=f)

    specfile = "git-command-specs.html" if writehtml else os.devnull
    with open(specfile, "at", encoding='utf-8') as f:
        print("%s" % html_header, file=f, end='')

    for cmd in git_commands:
        # If it's not a command at all, skip it
        if cmd in git_commands_not_command:
            continue

        print(cmd)
        rawHelp, rawHelpAll = run_git_help(cmd)
        if cmd in git_commands_adhoc_help:
            continue # ignore for now
        usage, opts = parseHelp(cmd, rawHelp, rawHelpAll)
        testHelp(cmd, usage, opts, rawHelp, rawHelpAll)

    with open(specfile, "at", encoding='utf-8') as f:
        print("%s" % html_footer, file=f, end='')

def testHelp(cmd, usage, opts, rawHelp, rawHelpAll):
    # if rawHelpAll doesn't exist, create it
    hasRawHelpAll = True
    if len(rawHelpAll) == 0:
        rawHelpAll = [x for x in rawHelp]
        hasRawHelpAll = False

    # Create help from usage and opts
    # First, add usage
    genHelp = []
    genHelpAll = []

    for line in usage:
        genHelp.append(line)
        genHelpAll.append(line)

    # Now turn opts into help
    for opt in opts:
        if opt[1] == "groupline":
            genHelp.append("")
            genHelpAll.append("")
        elif opt[1].startswith("textline: "):
            genHelp.append(opt[1][10:])
            genHelpAll.append(opt[1][10:])
        else:
            # Get the pieces of the entry; use defaults for missing pieces
            shortname = ""
            longname = ""
            argument = ""
            argtype = ""
            helptext = ""
            hidden = False
            optional = False
            numopt = False
            for entry in opt:
                if entry.startswith("shortname: "):
                    shortname = entry[11:]
                elif entry.startswith("longname: "):
                    longname = entry[10:]
                elif entry.startswith("argument: "):
                    argument = entry[10:]
                elif entry == "hidden":
                    hidden = True
                elif entry == "optional":
                    optional = True
                elif entry.startswith("help: "):
                    helptext = entry[7:-1]
                elif entry.startswith("type: "):
                    argtype = entry[6:]
                elif entry == "numopt":
                    numopt = True
                elif entry.startswith("option"):
                    optname = ""
                    if len(entry) > 7:
                        optname = entry[7:]
                else:
                    raise Exception("unknown", entry, opt)

            # Assemble shortname + longname + argument
            optarg = ""
            if shortname != "":
                optarg = optarg + "-" + shortname
            if longname != "":
                if optarg != "":
                    optarg = optarg + ", "
                optarg = optarg + "--" + longname
            if numopt:
                optarg = optarg + "-NUM"
            if argument != "":
                if not optional:
                    optarg = optarg + " "
                optarg = optarg + argument

            # Output option line, respecting both comment-column margin and
            # end-of-line margin
            output = ["    " + optarg, helptext]
            while len(output) > 0:
                line = output[0]
                output[0] = ""

                # If there is room on the line to add text, do so (otherwise we
                # just output this line as-is)
                if len(line) < 25:

                    # If there is nothing left to join, we're done, consume the buffer
                    if len(output[1]) == 0:
                        del output[0:2]

                    # Pad line and join as much remaining text as will fit
                    else:
                        line = line + " "*(26-len(line))

                        # If all the text fits on one line, do so, and consume the buffer
                        if len(line) + len(output[1]) < 127:
                            line = line + output[1]
                            del output[0:2]

                        # Otherwise, put as much on this line, save the rest for future lines
                        else:
                            lastspace = output[1].rfind(" ", 0, 54)
                            line = line + output[1][0:lastspace].rstrip()
                            output[0] = ""
                            output[1] = output[1][lastspace:].lstrip()

                # Output the built line
                genHelpAll.append(line)
                if not hidden:
                    genHelp.append(line)

            if 0:
                # Put help on the same line if it fits, otherwise the next line
                # This is commented-out for now, because Git doesn't actually do this
                # wrapping.
                optline = "    " + optarg
                overlong = len(optline) >= 25
                if not overlong:
                    if helptext != "":
                        optline = optline + " "*(26-len(optline)) + helptext

                genHelpAll.append(optline)
                if not hidden:
                    genHelp.append(optline)

                # If we have to wrap it, we wrap even if there actually is no helptext
                if overlong:
                    wrapline = ""
                    if helptext != "":
                        wrapline = " "*26 + helptext
                    genHelpAll.append(wrapline)
                    if not hidden:
                        genHelp.append(wrapline)

    if len(opts) > 0:
        genHelp.append("")
        genHelpAll.append("")

    testhelpf = "testhelp.txt" if writetest else os.devnull
    with open(testhelpf, "at", encoding='utf-8') as f:
        print("===================", file=f)
        print(cmd, file=f)
        print("----------- old:", file=f)
        for L in rawHelp:
            print(L, file=f)
        print("----------- new:", file=f)
        for L in genHelp:
            print(L, file=f)
        if hasRawHelpAll:
            print("----------- old:", file=f)
            for L in rawHelpAll:
                print(L, file=f)
            print("----------- new:", file=f)
            for L in genHelpAll:
                print(L, file=f)

        # Compare
        print("-----------", file=f)
        fatal = False
        if len(genHelp) != len(rawHelp):
            print("Error: real -h has %d lines, gen -h has %d lines" % (len(rawHelp), len(genHelp)), file=f)
            fatal = True
        else:
            diffline = ""
            for a, b in zip(genHelp, rawHelp):
                if a != b:
                    diffline = '"' + a + '" vs "' + b + '"'
                    break
            if diffline != "":
                print("Error: real -h does not match gen -h", file=f)
                print("First error: %s" % diffline, file=f)
                fatal = True

        if hasRawHelpAll:
            if len(genHelpAll) != len(rawHelpAll):
                print("Error: real --help-all has %d lines, gen --help-all has %d lines" % (len(rawHelp), len(genHelp)), file=f)
                fatal = True
            else:
                diffline = ""
                for a, b in zip(genHelpAll, rawHelpAll):
                    if a != b:
                        diffline = '"' + a + '" vs "' + b + '"'
                        break
                if diffline != "":
                    print("Error: real --help-all does not match gen --help-all", file=f)
                    print("First error: %s" % diffline, file=f)
                    fatal = True

        if fatal:
            raise Exception("mismatch between original and generated")
        else:
            print("Generated matches original", file=f)

# Split a line containing an option into its pieces. Return None if
# the line does not contain an option
def parseOptionLine(line):
    if len(line) == 0 or line.lstrip()[0] != '-':
        return None

    # Arguments are usually allowed, but there are some cases where
    # we can't have an argument
    argumentAllowed = True

    # See if we have an unusual shortopt name that's really a metadata
    # description of some non-standard option. A single-letter
    # option is normally followed by one of " ,=[<", since those
    # either separators or the beginning of an argument for a shortopt.
    # So look for anything else. Also, these don't have arguments
    # as far as I know
    shortname = ""
    match = re.match(r'\s+(-[a-zA-Z0-9][^ ,\[<]+)(.*)$', line)
    if match:
        shortname = match.group(1)
        line = match.group(2)
        argumentAllowed = False

    # See if we have a normal shortopt name. However, it's an
    # error if we already had one from above
    match = re.match(r'\s+-([a-zA-Z0-9])(.*)$', line)
    if match:
        if shortname != "":
            return None
        shortname = match.group(1)
        line = match.group(2)

    # see if there is a longname (we may have a ", " preamble left over)
    longname = ""
    match = re.match(r'(\s+|,\s)--([a-zA-Z0-9-)]+)(.*)$', line)
    if match:
        longname = match.group(2)
        line = match.group(3)

    # There must be an option, or this is not really an option line
    if shortname == "" and longname == "":
        return None

    # If there is an argument, it either is space-separated or
    # it has a leading '=' (possibly preceded by "["). If it has
    # a leading '=', it's optional.
    argument = ""
    argtype = "bool"
    optional = False

    if argumentAllowed:
        match = re.match(r'(\s|=|\[|\[=)\S', line)
        if match:
            argtype = "string"

            # If it begins with a space, the argument runs until the next space
            if match.group(1) == ' ':
                match = re.match(r'\s(\S+)(.*)$', line)
                if match:
                    argument = match.group(1)
                    line = match.group(2)
                else:
                    raise Exception("bad parse for %s" % rawline)

            # Otherwise, get the entire string that was attached to the
            # option.
            else:
                match = re.match(r'(\S+)(.*)$', line)
                if not match:
                    raise Exception("bad parse for '%s' in %s" % (line, rawline))
                argument = match.group(1)
                optional = True if (argument[0:1] == '=' or argument[0:1] == '[') else False
                line = match.group(2)

            # Some arguments aren't strings. Let's guess at it
            if re.search(r'<num>|<n>', argument):
                argtype = 'int'

    # Anything else must be the help
    helptext = line.lstrip()

    # Return the parsed line
    optlist = [shortname, longname, argument, argtype, optional, helptext]
    return optlist

# Return true if the line contains an option with no help text
def isOptionNoHelp(line):
    optlist = parseOptionLine(line)
    if optlist is None:
        return False
    if optlist[5] != "":
        return False

    # It's an option and there's no help text at the end
    return True

def parseHelp(cmd, rawHelp, rawHelpAll):
    usage = []
    options = []
    hidden = []
    inUsage = True
    firstline = True

    # make copies so we don't trash the caller's data
    rawHelp = [x for x in rawHelp]
    rawHelpAll = [x for x in rawHelpAll]

    # Make sure we have a superset for rawHelpAll
    if len(rawHelpAll) == 0:
        rawHelpAll = [x for x in rawHelp]

    while len(rawHelp) > 0 and len(rawHelpAll) > 0:

        # Consume next line. If it's only in rawHelpAll, then
        # this is a hidden line, remember that
        line = rawHelpAll[0]
        rawHelpAll = rawHelpAll[1:]

        isHidden = False
        if rawHelp[0] == line:
            rawHelp = rawHelp[1:]
        else:
            isHidden = True

        # See if we went past the end of the usage block
        if inUsage and not firstline:
            if line.startswith('    -'):
                inUsage = False
        firstline = False

        # Record this line in the proper block
        if inUsage:
            usage.append(line)
        else:
            options.append(line)
            hidden.append(isHidden)

    # For commands that are just usage and no options, write them
    # to a separate file
    if len(options) == 0:
        usageonlyf = "usageonly.txt" if debuglogs else os.devnull
        with open(usageonlyf, "at", encoding='utf-8') as f:
            print("--------------------", file=f)
            print(cmd, file=f)
            for L in usage:
                print(L, file=f)

    # For commands that have options, show all the ones that
    # don't end in a blank line
    if len(options) > 0 and len(usage[-1]) > 0:
        usagenonblankf = "usagenonblank.txt" if debuglogs else os.devnull
        with open(usagenonblankf, "at", encoding='utf-8') as f:
            print("--------------------", file=f)
            print(cmd, file=f)
            for L in usage:
                print(L, file=f)

    # If usage doesn't end with a blank line, we may have accidentally assigned
    # option-specification lines to the usage block. Undo that.
    # However, we only do this if we actually found some options.
    if len(options) > 0:
        while len(usage[-1]) > 0 and not usage[-1].startswith("usage:"):
            options.insert(0, usage[-1])
            hidden.insert(0, False)
            usage = usage[:-1]

    # Drop blank lines at the end of options
    while len(options) > 0 and len(options[-1]) == 0:
        options = options[:-1]
        hidden = hidden[:-1]

    # Join split help lines back with their option. This has to join empty
    # succeeding lines to an overlong option, not just non-empty help lines
    # (evidently a quirk in how Git internal help is printed).
    optionsraw = [x for x in options]
    hiddenraw = [x for x in hidden]
    options = []
    hidden = []
    for L, H in zip(optionsraw, hiddenraw):
        # If blank line and previous line is option line, drop the blank line
        # (it's an artifact of the help output process)
        if len(L) == 0 and isOptionNoHelp(options[-1]):
            pass

        # If this looks like a tabstopped comment line and the previous line
        # is an option line, join it to the option line
        elif re.match(r'\s{25}', L[1:]) and isOptionNoHelp(options[-1]):
            options[-1] = options[-1] + L[24:]

        # Otherwise, keep it
        else:
            options.append(L)
            hidden.append(H)

    # Parse options line by line
    opts = []
    for line, isHidden in zip(options, hidden):
        opt = ["option"]

        # If there is a blank line, create an opt to hold it
        if len(line) == 0:
            opt.append("groupline")
            opts.append(opt)
            continue

        # If this is a nonblank line that's clearly not an option, then
        # create an opt to hold it
        if line.lstrip()[0] != '-':
            opt.append("textline: %s" % line)
            opts.append(opt)
            continue

        # Parse the option line - at this point, we're sure it's an option line
        optlist = parseOptionLine(line)
        if optlist is None:
            raise Exception("bad parse for %s" % line)
        (shortname, longname, argument, argtype, optional, helptext) = optlist

        if shortname != "":
            if shortname == "-NUM":
                opt.append("numopt")
            else:
                opt.append("shortname: %s" % shortname)
        if longname != "":
            opt.append("longname: %s" % longname)
        if isHidden:
            opt.append("hidden")

        if argument != "":
            opt.append("argument: %s" % argument)
        if optional:
            opt.append("optional")
        if argtype != "":
            opt.append("type: %s" % argtype)

        if helptext != "":
            opt.append("help: \"%s\"" % helptext)

        # Create a name for the option - turn hyphens into camel-case text,
        # and make sure the characters are suitable for a language identifer
        optname = longname if longname else shortname
        optname = "NUM" if optname == "-NUM" else optname # hack
        # print(cmd, optname)

        words = optname.split('-')
        optname = ""
        for w in words:
            optname += w[0].upper() + w[1:]
        optname = optname[0].lower() + optname[1:]
        if re.search(r'[^_a-zA-Z0-9]', optname):
            raise Exception("not a valid id: %s" % optname)
        opt[0] = "option %s" % optname

        # Add our option to the list
        opts.append(opt)

    # We need an identifier version of cmd
    words = cmd.replace(' ', '-').split('-')
    cmdId = ""
    for w in words:
        cmdId += w[0].upper() + w[1:]
    cmdId = cmdId[0].lower() + cmdId[1:]
    if re.search(r'[^_a-zA-Z0-9]', cmdId):
        raise Exception("not a valid id: %s" % cmdId)
    # print("turned %s into %s" % (cmd, cmdId))

    # Output our parsed data
    parsehelpf = "parsehelp.txt" if writeparse else os.devnull
    with open(parsehelpf, "at", encoding='utf-8') as f:
        print("===================", file=f)
        print(cmd, file=f)
        print("-----------", file=f)
        for L in usage:
            print(L, file=f)
        print("-----------", file=f)
        for L in optionsraw:
            print(L, file=f)
        print("-----------", file=f)
        for L in options:
            print(L, file=f)
        print("-----------", file=f)
        print("command %s" % cmdId, file=f)
        for opt in opts:
            optname = opt[0]
            # print("    option", file=f)
            print("    %s" % optname, file=f)
            for o in opt[1:]:
                print("        %s" % o, file=f)

    specfile = "git-command-specs.txt" if writespecs else os.devnull
    with open(specfile, "at", encoding='utf-8') as f:
        print("command %s \"%s\"" % (cmdId, cmd), file=f)
        print("    usage", file=f)
        usagetrim = [x for x in usage]
        while len(usagetrim) > 0 and len(usagetrim[-1]) == 0:
            usagetrim = usagetrim[:-1]
        for L in usagetrim:
            print("        \"%s\"" % L, file=f)
        for opt in opts:
            optname = opt[0]
            # print("    option", file=f)
            print("    %s" % optname, file=f)
            for o in opt[1:]:
                print("        %s" % o, file=f)

    def escape(S):
        S = S.replace('<', '\\<')
        S = S.replace('[', '\\[')
        return S

    specfile = "git-command-specs.md" if writemarkdown else os.devnull
    with open(specfile, "at", encoding='utf-8') as f:
        print("_command_ **%s** `\"%s\"` {\\" % (cmdId, cmd), file=f)

        usagetrim = [x for x in usage]
        while len(usagetrim) > 0 and len(usagetrim[-1]) == 0:
            usagetrim = usagetrim[:-1]
        print("&#160;&#160;&#160;&#160;_usage_ { ", file=f, end='')
        if len(usagetrim) == 1:
            print("\"%s\" }\\" % escape(usagetrim[0]), file=f)
        else:
            print("\\", file=f)
            for L in usagetrim:
                print("&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;\"%s\",\\" % escape(L), file=f)
            print("&#160;&#160;&#160;&#160;}\\", file=f)

        for opt in opts:
            optnametag = opt[0]
            if optnametag == "option":
                if opt[1] == "groupline":
                    continue
                elif opt[1].startswith("textline: "):
                    continue
                raise Exception("what? %s" % opt)
            shortname = ""
            longname = ""
            argument = ""
            hidden = False
            optional = False
            helptext = ""
            argtype = ""
            numopt = True
            for entry in opt[1:]:
                if entry.startswith("shortname: "):
                    shortname = entry[11:]
                elif entry.startswith("longname: "):
                    longname = entry[10:]
                elif entry.startswith("argument: "):
                    argument = entry[10:]
                elif entry == "hidden":
                    hidden = True
                elif entry == "optional":
                    optional = True
                elif entry.startswith("help: "):
                    helptext = entry[7:-1]
                elif entry.startswith("type: "):
                    argtype = entry[6:]
                elif entry == "numopt":
                    numopt = True
            match = re.match(r'option (.+)$', optnametag)
            if not match:
                raise Exception("I expected better: %s" % optnametag)
            optname = match.group(1)
            print("&#160;&#160;&#160;&#160;_option_ **%s** _%s_ {" % (optname, argtype), file=f, end='')
            if shortname != "" and longname != "":
                optpattern = "%s|%s" % (longname, shortname)
            elif shortname == "":
                optpattern = "%s" % longname
            else:
                optpattern = "%s" % shortname
            print(" \"%s\"" % optpattern, file=f, end='')
            if hidden:
                print(", _hidden_", file=f, end='')
            if argument != "":
                print(", _arg_=\"%s\"" % escape(argument), file=f, end='')
            if optional:
                print(", _optional_", file=f, end='')
            if helptext != "":
                print(", _help_=\"%s\"" % helptext, file=f, end='')
            print(" }\\", file=f)

        print("}\n", file=f)

    def escapehtml(S):
        S = S.replace('&', '&amp;')
        S = S.replace('<', '&lt;')
        return S

    specfile = "git-command-specs.html" if writehtml else os.devnull
    with open(specfile, "at", encoding='utf-8') as f:
        print("<p><em>command</em> <strong>%s</strong> <code>\"%s\"</code> {<br>" % (cmdId, cmd), file=f)

        usagetrim = [x for x in usage]
        while len(usagetrim) > 0 and len(usagetrim[-1]) == 0:
            usagetrim = usagetrim[:-1]
        print("<span class=\"tabstop\"><em>usage</em> { ", file=f, end='')
        if len(usagetrim) == 1:
            print("<code>\"%s\"</code> }<br>" % escapehtml(usagetrim[0]), file=f)
        else:
            print("<br>", file=f)
            for L in usagetrim:
                print("<span class=\"tabstop\"><span class=\"tabstop\"><code>\"%s\"</code>, <br>" % escapehtml(L), file=f)
            print("<span class=\"tabstop\">}<br>", file=f)

        for opt in opts:
            optnametag = opt[0]
            if optnametag == "option":
                if opt[1] == "groupline":
                    print("<span class=\"tabstop\"><em>groupline</em><br>", file=f)
                    continue
                elif opt[1].startswith("textline: "):
                    print("<span class=\"tabstop\"><em>textline</em> { \"%s\" }<br>" % escapehtml(opt[1][10:]), file=f)
                    continue
                raise Exception("what? %s" % opt)
            shortname = ""
            longname = ""
            argument = ""
            hidden = False
            optional = False
            helptext = ""
            argtype = ""
            numopt = True
            for entry in opt[1:]:
                if entry.startswith("shortname: "):
                    shortname = entry[11:]
                elif entry.startswith("longname: "):
                    longname = entry[10:]
                elif entry.startswith("argument: "):
                    argument = entry[10:]
                elif entry == "hidden":
                    hidden = True
                elif entry == "optional":
                    optional = True
                elif entry.startswith("help: "):
                    helptext = entry[7:-1]
                elif entry.startswith("type: "):
                    argtype = entry[6:]
                elif entry == "numopt":
                    numopt = True
            match = re.match(r'option (.+)$', optnametag)
            if not match:
                raise Exception("I expected better: %s" % optnametag)
            optname = match.group(1)
            print("<span class=\"tabstop\"><em>option</em> <strong>%s</strong> <em>%s</em> { " % (optname, argtype), file=f, end='')
            if shortname != "" and longname != "":
                optpattern = "%s|%s" % (longname, shortname)
            elif shortname == "":
                optpattern = "%s" % longname
            else:
                optpattern = "%s" % shortname
            print(" <code>\"%s\"</code>" % optpattern, file=f, end='')
            if hidden:
                print(", <em>hidden</em>", file=f, end='')
            if argument != "":
                print(", <em>arg</em>=\"%s\"" % escapehtml(argument), file=f, end='')
            if optional:
                print(", <em>hidden</em>", file=f, end='')
            if helptext != "":
                print(", <em>help</em>=\"%s\"" % escapehtml(helptext), file=f, end='')
            print(" }<br>", file=f)

        print("}<p>", file=f)

    return usage, opts

def run_git_usage(cmd):
    rawUsage = []
    rawhelp = "rawhelp.txt" if writeraw else os.devnull
    with open(rawhelp, "at", encoding='utf-8') as f:
        print("-----------------------------------", file=f)

        cmdline = "git %s -h" % cmd
        print(cmdline, file=f)
        print("--------", file=f)
        for line in run_command(cmdline):
            line = utf8_to_string(line).rstrip()
            print(line, file=f)
            rawUsage.append(line)

    return rawUsage

def run_git_help(cmd):
    rawHelp = []
    rawHelpAll = []
    rawhelp = "rawhelp.txt" if writeraw else os.devnull
    with open(rawhelp, "at", encoding='utf-8') as f:
        print("-----------------------------------", file=f)

        cmdline = "git %s -h" % cmd
        print(cmdline, file=f)
        print("--------", file=f)
        for line in run_command(cmdline):
            line = utf8_to_string(line).rstrip()
            print(line, file=f)
            rawHelp.append(line)

        # Only call --help-all on commands that support it
        if cmd not in git_commands_no_help_all:
            print("--------", file=f)
            cmdline = "git %s --help-all" % cmd
            print(cmdline, file=f)
            print("--------", file=f)
            for line in run_command(cmdline):
                line = utf8_to_string(line).rstrip()
                line = line.rstrip()
                print(line, file=f)
                rawHelpAll.append(line)

    return rawHelp, rawHelpAll

def run_command(cmd):
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    #return iter(p.stdout.readline, b'')
    return iter(p.stdout.readline, b'')

# This safely turns a byte sequence presumed to be UTF8 into a Python unicode string.
# Any non-Unicode characters are escaped in \xHH values (H is a hex digit, and we assume
# that normal strings won't have a \xHH sequence in them. If they do, we should consider
# escaping any '\' character seen.
# This could be written in a more efficient fashion, but we don't expect to have very many
# strings with illegal characters
def utf8_to_string(raw, diag=None):
    return codecs.decode(raw, encoding='utf-8', errors='strict')
    for kind in ('utf-8', 'cp1252'):
        if kind == 'utf-8':
            try:
                s = codecs.decode(raw, encoding='utf-8', errors='strict')
            except Exception as inst:
                s = None
        elif kind == 'cp1252':
            try:
                s = codecs.decode(raw, encoding='cp1252', errors='strict')
                for c in s:
                    if ord(c) == 10 or ord(c) == 13 or (ord(c) >= 32 and ord(c) < 127):
                        continue
                    if c in 'ãéô“”‘’üöä':
                        continue
                    s = None
                    break
                if s is not None:
                    if diag:
                        diag("decoded %s as cp1252: %s" % (raw.hex(), s))
            except Exception as inst:
                s = None

        # We have a string that looks sane
        if s is not None:
            return s

    # The string is messed up, assume UTF-8 and encode non-UTF-8 character accordingly
    # A better answer would be to find the encoding with the fewest errors
    out = ""
    e = len(raw)
    p = 0
    s = p
    while p < e:
        # 0xxxxxxx
        if (raw[p] & 0b10000000) == 0:
            p += 1
        # 110xxxxx 10xxxxxx
        elif (raw[p] & 0b11100000) == 0b11000000 and (raw[p+1] & 0b11000000) == 0b10000000:
            p += 2
        # 1110xxxx 10xxxxxx 10xxxxxx
        elif (raw[p] & 0b11110000) == 0b11100000 and (raw[p+1] & 0b11000000) == 0b10000000 and (raw[p+2] & 0b11000000) == 0b10000000:
            p += 3
        # 11110xxx 10xxxxxx 10xxxxxx 10xxxxxx
        elif (raw[p] & 0b11111000) == 0b11110000 and (raw[p+1] & 0b11000000) == 0b10000000 and (raw[p+2] & 0b11000000) == 0b10000000 and (raw[p+3] & 0b11000000) == 0b10000000:
            p += 4

        # oops
        else:
            if p > s:
                out = out + raw[s:p].decode('utf-8')
            out = out + "\\x" + raw[p:p+1].hex()
            if diag:
                diag("skipping bytes[%d]=%02x" % (p, raw[p]))
            p += 1
            s = p
    if p > s:
        out = out + raw[s:p].decode('utf-8')

    if diag:
        diag("decoded as utf8-escape: %s" % out)
    return out

html_header = """
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" lang="" xml:lang="">
<head>
  <meta charset="utf-8" />
  <meta name="generator" content="pandoc" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=yes" />
  <meta name="author" content="Brian Fitzgerald" />
  <title>GSGit: Git in Go</title>
  <style type="text/css">
      code{white-space: pre-wrap;}
      span.smallcaps{font-variant: small-caps;}
      span.underline{text-decoration: underline;}
      div.column{display: inline-block; vertical-align: top; width: 50%;}
      span.tabstop{margin: 0 0 0 1.5em;}
  </style>
  <!--[if lt IE 9]>
    <script src="//cdnjs.cloudflare.com/ajax/libs/html5shiv/3.7.3/html5shiv-printshiv.min.js"></script>
  <![endif]-->
</head>
<body>
<h1 id="git-command-spec">Git command spec</h1>
<p>pretty form</p>
"""

html_footer = """
</body>
</html>
"""

# -----------------------------------------------------------------------------------------------

# This is just so that we can write code in what seems reasonable rather than
# in the order Python execution needs it.
if __name__ == '__main__':
    main()
