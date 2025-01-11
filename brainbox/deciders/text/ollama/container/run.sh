#!/bin/bash

# Check if there are no command line arguments
if [ $# -eq 0 ]; then
    # Run /bin/ollama serve without arguments
    /bin/ollama serve
else
    # Run /bin/ollama serve in the background
    /bin/ollama serve &

    sleep 1

    # Run /bin/ollama with the provided command line arguments
    /bin/ollama "$@"
fi
