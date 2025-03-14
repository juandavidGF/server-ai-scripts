import sys
import os
from pathlib import Path
import torch
import argparse
from PIL import Image
from transformers import AutoProcessor, LlavaForConditionalGeneration

def rename_images(folder_path):
    """Renames images in a folder to sequential names like image1.jpg, image2.jpg, etc."""
    valid_extensions = ('.jpg', '.jpeg', '.png')
    images = [f for f in os.listdir(folder_path) if f.lower().endswith(valid_extensions)]
    images.sort()

    for index, filename in enumerate(images, start=1):
        ext = os.path.splitext(filename)[1]
        new_filename = f"image{index}{ext}"
        old_file = os.path.join(folder_path, filename)
        new_file = os.path.join(folder_path, new_filename)

        if os.path.exists(new_file):
            print(f"Warning: {new_file} already exists, skipping rename of {filename}")
            continue
        
        os.rename(old_file, new_file)
        print(f'Renamed: {old_file} → {new_file}')

def generate_captions(folder_path, keyword):
    """Generates detailed captions for images using the LLaVA 13B model, specifically for the keyword entity."""
    print("Loading model...")
    
    model_id = "llava-hf/llava-1.5-13b-hf"
    
    # Load processor and model
    processor = AutoProcessor.from_pretrained(model_id)
    model = LlavaForConditionalGeneration.from_pretrained(
        model_id, 
        torch_dtype=torch.float16,
        low_cpu_mem_usage=True,
        device_map="auto"
    )

    # Clear prompt with an example for the keyword entity
    prompt_text = (
        f"Describe the {keyword} man in this image in four detailed sentences. "
        f"First sentence: style and type of the image (e.g., painting, photo). "
        f"Second sentence: what the {keyword} man is doing. "
        f"Third sentence: his appearance and specific details. "
        f"Fourth sentence: composition, keywords separated by commas, precise layout. "
        f"Example: 'photo of {keyword} man, he is swinging a sword in a battle stance. He wears a futuristic silver suit with glowing blue stripes and a spiked helmet. The composition features dynamic lines, vibrant colors, action pose, dark stormy background.'"
    )

    valid_extensions = ('.jpg', '.jpeg', '.png')
    for filename in os.listdir(folder_path):
        if filename.lower().endswith(valid_extensions):
            image_path = os.path.join(folder_path, filename)
            try:
                print(f"Processing {image_path}...")
                image = Image.open(image_path).convert("RGB")  # Ensure RGB format
                
                # Structure conversation for the model
                conversation = [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt_text},
                            {"type": "image"},
                        ],
                    },
                ]
                
                # Apply chat template to format the prompt
                prompt = processor.apply_chat_template(conversation, add_generation_prompt=True)
                
                # Process inputs
                inputs = processor(
                    images=image, 
                    text=prompt, 
                    return_tensors="pt"
                ).to(model.device, torch.float16)
                
                # Debug: Inspect inputs
                print(f"Inputs for {filename}: {inputs.keys()}")

                # Generate caption with parameters for richer output
                with torch.no_grad():
                    output = model.generate(
                        **inputs,
                        max_new_tokens=300,  # Increased for more detail
                        do_sample=True,      # Sampling for creativity
                        temperature=0.6,     # Slightly lower for coherence with detail
                        top_p=0.9            # Nucleus sampling for quality
                    )
                
                # Decode the output, skipping the input tokens
                caption = processor.decode(output[0][len(inputs["input_ids"][0]):], skip_special_tokens=True)
                
                # Remove "ASSISTANT:" prefix if present
                if caption.startswith("ASSISTANT:"):
                    caption = caption[len("ASSISTANT:"):].strip()
                
                # Post-process caption to ensure the keyword is included
                if keyword not in caption:
                    if "man" in caption.lower():
                        # Replace "man" with "keyword man" (case-insensitive)
                        caption = caption.replace("man", f"{keyword} man").replace("Man", f"{keyword} man")
                    else:
                        # Prepend "keyword man" if neither keyword nor "man" is present
                        caption = f"{keyword} man " + caption
                
                # Debug: Print raw output
                print(f"Raw caption for {filename}: {caption}")
                
                # Save caption
                caption_file = os.path.splitext(image_path)[0] + '.txt'
                with open(caption_file, 'w', encoding='utf-8') as f:
                    f.write(caption)
                print(f'Generated caption saved to: {caption_file}')
            except Exception as e:
                print(f"Error processing {image_path}: {e}")
                import traceback
                traceback.print_exc()

if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Process images and generate captions.')
    parser.add_argument('--rename', action='store_true', help='Rename images to sequential names')
    parser.add_argument('--keyword', type=str, default="p3r50n",
                        help=f'Keyword to use in captions (default: p3r50n)')
    parser.add_argument('--folder', type=str, default='../images',
                        help='Path to the folder containing images (default: ../images)')
    
    # Parse arguments
    args = parser.parse_args()
    
    folder_path = args.folder
    keyword = args.keyword
    
    print(f"Using keyword: {keyword}")
    print(f"Using folder: {folder_path}")
    
    # Check if rename flag is provided
    if args.rename:
        rename_images(folder_path)
        print("Images renamed successfully.")
    
    # Always run caption generation
    print("Generating captions...")
    generate_captions(folder_path, keyword)
