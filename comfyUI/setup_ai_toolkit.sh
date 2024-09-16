#!/bin/bash

# Clone the repository
git clone https://github.com/ostris/ai-toolkit.git

# Change directory to ai-toolkit
cd ai-toolkit || { echo "Failed to enter ai-toolkit directory"; exit 1; }

# Update submodules
git submodule update --init --recursive

# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
if [[ "$OSTYPE" == "linux-gnu"* || "$OSTYPE" == "darwin"* ]]; then
    # For Linux and macOS
    source venv/bin/activate
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    # For Windows Git Bash
    .\\venv\\Scripts\\activate
else
    echo "Unsupported OS. Please activate the virtual environment manually."
    exit 1
fi

# Install torch first
pip3 install torch

# Install other requirements
pip3 install -r requirements.txt

# Notify the user
echo "Setup completed!"
