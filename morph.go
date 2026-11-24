package main

import (
	"fmt"
	"log"
	"os"
	"os/exec"
)

func main() {
	cmd := exec.Command("uv", "run", "ah")

	cmd.Dir = "/home/mashce/Work/agent_harness/"

	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr

	if err := cmd.Run(); err != nil {
		log.Fatalf("uv execution failed: %v", err)
	}

	fmt.Println("uv project finished successfully")
}
