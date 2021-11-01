// gen-flag.go
// Generate command-line using the flag package from the Go standard library

package main

import (
	"bufio"
	"fmt"
	"log"
	"os"
)

func main() {
	if len(os.Args) < 2 {
		fmt.Println("No specfile supplied")
		os.Exit(1)
	}
	specfile := os.Args[1]

	fmt.Printf("Reading from %s\n", specfile)
	specs := readspecs(specfile)
	fmt.Printf("We have %d commands\n", len(specs))
	genCommands(specs)
}

// ----------------------------------------------------------------------------

func genCommands(specs []entry) {
	outfile := "goparser.go"
	f, err := os.Create(outfile)
	if err != nil {
		log.Fatalf("Failed to create %s: %s\n", outfile, err)
	}
	w := bufio.NewWriter(f)
	w.WriteString(fmt.Sprintf("// %s\n", outfile))

	w.Flush()
	f.Close()
}
