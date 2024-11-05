import sys
import os
from pathlib import Path
import torch
from PIL import Image
from transformers import pipeline, AutoProcessor
import re

def rename_images(folder_path):
    # Supported image extensions
    valid_extensions = ('.jpg', '.jpeg', '.png')
    
    # List to hold all images
    images = []

    # Iterate through the files
    for filename in os.listdir(folder_path):
        if filename.lower().endswith(valid_extensions):
            images.append(filename)

    # Sort the images
    images.sort()

    # Dictionary to track renamed images
    renamed_images = {}

    # Rename files with new sequential numbers
    for index, filename in enumerate(images, start=1):
        # Get the original file extension
        ext = os.path.splitext(filename)[1]
        new_filename = f"image{index}{ext}"  # Keep the original extension
        old_file = os.path.join(folder_path, filename)
        new_file = os.path.join(folder_path, new_filename)
        
        # Check if the target file already exists
        if os.path.exists(new_file):
            print(f"Warning: {new_file} already exists, skipping rename of {filename}")
            continue
        
        # Rename file
        os.rename(old_file, new_file)
        renamed_images[filename] = new_filename
        print(f'Renamed: {old_file} to {new_file}')

    return renamed_images

def generate_captions(folder_path):
    # Initialize model
    model_id = "llava-hf/llava-1.5-7b-hf"
    
    # Check if model is already downloaded
    model_cache_dir = Path.home() / ".cache" / "huggingface" / "hub" / "models--llava-hf--llava-1.5-7b-hf"
    if not model_cache_dir.exists() or not any(model_cache_dir.iterdir()):
        print(f"Model not found in cache. Downloading model {model_id}...")
    else:
        print(f"Model found in cache at {model_cache_dir}. Using existing model.")
    
    pipe = pipeline("image-to-text", model=model_id)
    processor = AutoProcessor.from_pretrained(model_id)
    
    # Set patch size and vision feature select strategy
    processor.patch_size = 16
    processor.vision_feature_select_strategy = "default"

    PROMPT = """
    Write a four sentence caption for this image. In the first sentence describe the style and type (painting, photo, etc) of the image. Describe in the remaining sentences the contents and composition of the image. Only use language that would be used to prompt a text to image model. Do not include usage. Comma separate keywords rather than using "or". Precise composition is important. Avoid phrases like "conveys a sense of" and "capturing the", just use the terms themselves.

    Good examples are:

    "Photo of an alien woman with a glowing halo standing on top of a mountain, wearing a white robe and silver mask in the futuristic style with futuristic design, sky background, soft lighting, dynamic pose, a sense of future technology, a science fiction movie scene rendered in the Unreal Engine."

    "A scene from the cartoon series Masters of the Universe depicts Man-At-Arms wearing a gray helmet and gray armor with red gloves. He is holding an iron bar above his head while looking down on Orko, a pink blob character. Orko is sitting behind Man-At-Arms facing left on a chair. Both characters are standing near each other, with Orko inside a yellow chestplate over a blue shirt and black pants. The scene is drawn in the style of the Masters of the Universe cartoon series."

    "An emoji, digital illustration, playful, whimsical. A cartoon zombie character with green skin and tattered clothes reaches forward with two hands, they have green skin, messy hair, an open mouth and gaping teeth, one eye is half closed."
    """.strip()
    
    # Process each image
    valid_extensions = ('.jpg', '.jpeg', '.png')
    for filename in os.listdir(folder_path):
        if filename.lower().endswith(valid_extensions):
            image_path = os.path.join(folder_path, filename)
            image = Image.open(image_path)
            
            # Define conversation
            conversation = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": PROMPT},
                        {"type": "image"},
                    ],
                },
            ]
            
            # Generate caption
            prompt = processor.apply_chat_template(conversation, add_generation_prompt=True)
            outputs = pipe(image, prompt=prompt, generate_kwargs={"max_new_tokens": 512})
            caption = outputs[0]['generated_text']
            
            # Save caption
            caption_file = os.path.splitext(image_path)[0] + '.txt'
            with open(caption_file, 'w', encoding='utf-8') as f:
                f.write(caption)
            print(f'Generated caption saved to: {caption_file}')

# Run the script
folder_path = 'images/Alextremo'
# rename_images(folder_path)  # First rename all images
generate_captions(folder_path)  # Then generate captions
