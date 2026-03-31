#!/usr/bin/env python3
import os
import sys

# Configuration
MODE = 'local'         # 'local' or 'npm'. Use local to test this script
PACKAGE_DIR = '.'      # Directory containing package.json
NPM_TOKEN = None       # Set for npm deployment

def run_cmd(cmd):
    print(f"> {cmd}")
    result = os.system(cmd)
    return result == 0

def main():
    print("Deploying TypeScript package")

    # Change to package directory
    original_dir = os.getcwd()
    os.chdir(PACKAGE_DIR)

    try:
        # 1. Run linter
        print("\n1. Running linter...")
        if not run_cmd("npm run lint"):
            print("Linting failed")
            sys.exit(1)

        # 2. Build TypeScript
        print("\n2. Building TypeScript...")
        if not run_cmd("npm run build"):
            print("Build failed")
            sys.exit(1)

        # 3. Deploy
        print(f"\n3. Deploying ({MODE} mode)...")

        if MODE == 'local':
            if run_cmd("npm pack"):
                print("Local package created")
            else:
                print("Failed to create local package")
                sys.exit(1)

        elif MODE == 'npm':
            if not NPM_TOKEN:
                print("Error: NPM_TOKEN not set")
                sys.exit(1)

            os.environ['NPM_TOKEN'] = NPM_TOKEN
            if run_cmd("npm publish"):
                print("Package published to npm")
            else:
                print("Failed to publish to npm")
                sys.exit(1)

        else:
            print(f"Error: Unknown mode {MODE}")
            sys.exit(1)

        print("\nDeployment completed successfully")

    finally:
        # Return to original directory
        os.chdir(original_dir)

if __name__ == '__main__':
    main()