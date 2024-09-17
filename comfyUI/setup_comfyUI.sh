#!/bin/bash

# Function to log messages
log_message() {
    echo "$(date): $1"
}

# Function to download file if it doesn't exist
download_if_not_exists() {
    local url="$1"
    local destination="$2"
    if [ ! -f "$destination" ]; then
        log_message "Downloading $(basename "$destination")"
        if [[ "$url" == *"huggingface.co"* && -n "$HF_TOKEN" ]]; then
            wget --header="Authorization: Bearer ${HF_TOKEN}" -O "$destination" "$url" || {
                log_message "Warning: Failed to download $(basename "$destination"). Continuing with the next step."
                return 1
            }
        else
            wget -O "$destination" "$url" || {
                log_message "Warning: Failed to download $(basename "$destination"). Continuing with the next step."
                return 1
            }
        fi
        log_message "Downloaded successfully: $(basename "$destination")"
    else
        log_message "File already exists, skipping download: $(basename "$destination")"
    fi
}

# Load environment variables from .env file and print them
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
    echo "Loaded environment variables from .env:"
else
    log_message "Error: .env file not found. Exiting."
    exit 1  # Exit if .env file is not found
fi

# Check for configuration parameter
if [ "$1" = "flux" ]; then
    FLUX_CONFIG=true
    log_message "Flux configuration enabled"
else
    FLUX_CONFIG=false
    log_message "Standard configuration"
fi

# Check for Hugging Face token
if [ -z "$HF_TOKEN" ]; then
    log_message "Error: HF_TOKEN environment variable not set. Exiting."
    exit 1  # Exit if HF_TOKEN is not set
else
    log_message "Hugging Face token detected"
fi

# Log current working directory
log_message "Set up init, Current working directory: $(pwd)"

# Clone ComfyUI if not already present under home directory
COMFY_DIR="$HOME/ComfyUI"
if [ ! -d "$COMFY_DIR" ]; then
    log_message "Cloning ComfyUI repository under home directory"
    if ! git clone https://github.com/comfyanonymous/ComfyUI.git "$COMFY_DIR"; then
        log_message "Error: Failed to clone ComfyUI repository. Exiting."
        exit 1
    fi
else
    log_message "ComfyUI repository already exists. Updating existing repository."
    cd "$COMFY_DIR"
    if ! git pull; then
        log_message "Error: Failed to update ComfyUI repository. Exiting."
        exit 1
    fi
fi

# Change to ComfyUI directory
cd "$COMFY_DIR"
log_message "Changed to ComfyUI directory: $COMFY_DIR"

# Set up virtual environment
log_message "Setting up virtual environment"
if ! python3 -m venv myenv; then
    log_message "Error: Failed to create virtual environment. Exiting."
    exit 1
fi
source myenv/bin/activate

# Install requirements
log_message "Installing Python requirements, I'm on: $(pwd)"
if ! pip install -r requirements.txt; then
    log_message "Error: Failed to install some Python requirements. Exiting."
    exit 1
fi

# Set up ComfyUI-Manager
log_message "Setting up ComfyUI-Manager"
mkdir -p custom_nodes
cd custom_nodes
log_message "Downloading ComfyUI-Manager on (I'm here): $(pwd)"
if [ ! -d "ComfyUI-Manager" ]; then
    if ! git clone https://github.com/ltdrdata/ComfyUI-Manager.git; then
        log_message "Error: Failed to clone ComfyUI-Manager. Exiting."
        exit 1
    fi
else
    cd ComfyUI-Manager
    if ! git pull; then
        log_message "Error: Failed to update ComfyUI-Manager. Exiting."
        exit 1
    fi
    cd ..
fi

# If ComfyUI-Manager directory exists, install its requirements
if [ -d "ComfyUI-Manager" ]; then
    cd ComfyUI-Manager
    log_message "Installing ComfyUI-Manager Python requirements, I'm on: $(pwd)"
    pip install -r requirements.txt || log_message "Warning: Failed to install some ComfyUI-Manager requirements. Continuing."
    cd "$COMFY_DIR"
fi

# # Install ngrok
# if ! command -v ngrok &> /dev/null; then
#     log_message "Installing ngrok"
#     curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
#     echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
#     if ! sudo apt-get update || ! sudo apt-get install -y ngrok; then
#         log_message "Warning: Failed to install ngrok. Continuing without it."
#     fi
# fi

# Download Stable Diffusion checkpoint
CHECKPOINTS_DIR="$COMFY_DIR/models/checkpoints"
log_message "Downloading Stable Diffusion checkpoint"
mkdir -p "$CHECKPOINTS_DIR"
download_if_not_exists "https://huggingface.co/runwayml/stable-diffusion-v1-5/resolve/main/v1-5-pruned-emaonly.ckpt" "$CHECKPOINTS_DIR/v1-5-pruned-emaonly.ckpt"

# Flux-specific configuration
if [ "$FLUX_CONFIG" = true ]; then
    log_message "Setting up Flux-specific configuration"

    # CLIP models
    CLIP_DIR="$COMFY_DIR/models/clip"
    mkdir -p "$CLIP_DIR"
    log_message "Downloading Flux-specific CLIP files"
    download_if_not_exists "https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/clip_l.safetensors" "$CLIP_DIR/clip_l.safetensors"
    download_if_not_exists "https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/t5xxl_fp16.safetensors" "$CLIP_DIR/t5xxl_fp16.safetensors"
    download_if_not_exists "https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/t5xxl_fp8_e4m3fn.safetensors" "$CLIP_DIR/t5xxl_fp8_e4m3fn.safetensors"

    # VAE model
    VAE_DIR="$COMFY_DIR/models/vae"
    mkdir -p "$VAE_DIR"
    log_message "Downloading Flux-specific VAE file"
    download_if_not_exists "https://huggingface.co/black-forest-labs/FLUX.1-schnell/resolve/main/ae.safetensors" "$VAE_DIR/ae.safetensors"

    UNET_DIR="$COMFY_DIR/models/unet"
    mkdir -p "$UNET_DIR"
    log_message "Downloading Flux-specific UNET file"
    download_if_not_exists "https://huggingface.co/black-forest-labs/FLUX.1-dev/resolve/main/flux1-dev.safetensors" "$UNET_DIR/flux1-dev.safetensors"

    

    # Flux checkpoint
    log_message "Downloading Flux-specific checkpoint"
    download_if_not_exists "https://huggingface.co/Comfy-Org/flux1-dev/resolve/main/flux1-dev-fp8.safetensors" "$CHECKPOINTS_DIR/flux1-dev-fp8.safetensors"
fi

# Start ComfyUI
log_message "Starting ComfyUI"
log_message "Final working directory: $(pwd)"
python main.py

log_message "ComfyUI Setup Script completed"