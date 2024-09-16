#!/bin/bash

# Check if project directory path is provided as an argument
if [ $# -eq 0 ]; then
    echo "Usage: $0 <project_directory>"
    exit 1
fi

# Extract project directory path from arguments
project_dir="$1"

# Create project directory
mkdir -p "$project_dir"
cd "$project_dir"

# Initialize Git
git init

# Generate .gitignore
npx gitignore node > .gitignore

# Initialize npm
npm init -y

# Install TypeScript and ts-node
npm install typescript ts-node --save-dev

# Install type definitions for Node.js
npm install @types/node --save-dev

# Generate tsconfig.json
npx tsc --init

# Install dotenv for environment variable management
npm install dotenv --save

# Create .env file
touch .env

# Create index.ts file with the specified content
echo ";(async () => {
  console.log('Hello World');
})();" > index.ts

# Associate index.ts as the main entry point in package.json
npm set-script start "ts-node index.ts"
# Add dev script to package.json
npm set-script dev "ts-node index.ts"

# Output success message
echo "TypeScript project initialized successfully in $project_dir!"