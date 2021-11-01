// gen-lib.go
// shared code for command-line generation with Go code

package main

import (
	"bufio"
	"fmt"
	"log"
	"os"
	"strings"
)

// A single command entry
type entry struct {
	cmdid string
	cmdname string
	usage []string
	opts []option
}

// A single option entry
type option struct {
	optkind string
	shortname string
	longname string
	argument string
	hidden bool
	optional bool
	helptext string
	argtype string
	numopt bool
	textline string // could overload with some other field
}

// ----------------------------------------------------------------------------

// Read the command-spec file into a data structure
// A file looks like this:
//    command add
//        usage
//            "usage: git add [<options>] [--] <pathspec>..."
//        option dryRun
//            shortname: n

func readspecs(specfile string) []entry {
	var cmds []entry
	f, err := os.Open(specfile)
	if err != nil {
		log.Fatalf("Couldn't open %s: %s\n", specfile, err)
	}

	r := bufio.NewScanner(f)
	n := 1

	// After the first time through, we have a pending lookahead
	// line from the previous parsing step, so we enter the first
	// time with an already-scanned line
	if !r.Scan() {
		fmt.Printf("empty file?\n")
    	os.Exit(1)
	}

	for {
		line := r.Text()
		if line == "" {
			if !r.Scan() {
				break
			}
			continue
		}
		//fmt.Printf("%d: %s\n", n, line)

        // We must be at a "command xxx" line. Parse into the pieces of
        // cmdid and cmdname, since we need both
        if !strings.HasPrefix(line, "command") {
        	fmt.Printf("expected 'command' in line %d: got %s\n", n, line)
        	os.Exit(1)
        }
        cmdid := line[8:]
        cmdname := cmdid
		i := strings.Index(cmdid, " \"")
		if i != -1 {
			cmdname = cmdid[i+2:len(cmdid)]
			cmdid = cmdid[:i]
		}
		//fmt.Printf("    cmdid=%s cmdname=%s\n", cmdid, cmdname)

		// Parse usage and options
		var usage []string
		var opts []option
		usage, n = readcmdusage(r, n)
		opts, n = readcmdoptions(r, n)

		// Add the completed entry
		var e entry
		e.cmdid = cmdid
		e.cmdname = cmdname
		e.usage = usage
		e.opts = opts

		cmds = append(cmds, e)
	}

	f.Close()
	return cmds
}

// Read the usage section
func readcmdusage(r *bufio.Scanner, n int) ([]string, int) {
	var usage []string

	// We expect a usage header
	// At this point, we have no pending lookahead, so we always get a line
	if !r.Scan() {
    	fmt.Printf("expected 'usage' but EOF at line %d\n", n)
    	os.Exit(1)
	}
	n += 1

	line := strings.TrimSpace(r.Text())
	if line != "usage" {
    	fmt.Printf("expected 'usage' in line %d: got %s\n", n, line)
    	os.Exit(1)
	}

	// Read usage until we see the first option, or the next command,
	// or
	for {
		n += 1
		if !r.Scan() {
			break
		}
		line = r.Text()
		if strings.HasPrefix(line, "option") || strings.HasPrefix(line, "command") {
			break
		}
		line = strings.TrimSpace(line)
		usage = append(usage, line[1:len(line)-1])
	}

	return usage, n
}

// Options go until EOF or we see another command
func readcmdoptions(r *bufio.Scanner, n int) ([]option, int) {
	var opts []option

	// We start out by knowing a line from the lookahead from a previous step
	for {
		line := strings.TrimSpace(r.Text())
		if strings.HasPrefix(line, "command") {
			break
		}

		if !r.Scan() {
			break
		}
		n += 1
		line = strings.TrimSpace(r.Text())

		if !strings.HasPrefix(line, "option") {
			fmt.Printf("expected option in line %d: got %s\n", n, line)
			os.Exit(1)
		}

		var opt option
		opt.optkind = "option"
		var groupline bool
		for {
			if strings.HasPrefix(line, "option") || strings.HasPrefix(line, "command") {
				break
			}
			if !r.Scan() {
				break
			}
			n += 1
			line = strings.TrimSpace(r.Text())
			if strings.HasPrefix(line, "shortname: ") {
				opt.shortname = line[11:]
			} else if strings.HasPrefix(line, "longname: ") {
				opt.longname = line[10:]
			} else if strings.HasPrefix(line, "argument: ") {
				opt.argument = line[10:]
			} else if line == "hidden" {
				opt.hidden = true
			} else if line == "optional" {
				opt.optional = true
			} else if strings.HasPrefix(line, "help: ") {
				opt.helptext = line[7:len(line)-1]
			} else if strings.HasPrefix(line, "type: ") {
				opt.argument = line[6:]
			} else if line == "numopt" {
				opt.numopt = true
			} else if line == "groupline" {
				groupline = true
			} else if strings.HasPrefix(line, "textline: ") {
				opt.textline = line[10:]
			} else {
				fmt.Printf("unknown text in line %d: %s\n", n, line)
			}
		}

		if groupline {
			opt.optkind = "groupline"
		} else if len(opt.textline) > 0 {
			opt.optkind = "textline"
		}

		opts = append(opts, opt)
	}

	return opts, n
}
