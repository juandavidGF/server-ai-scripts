import sys
import os
from pathlib import Path
import torch
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

def generate_captions(folder_path):
    """Generates detailed captions for images using the LLaVA 13B model, specifically for TOK man."""
    print("Loading model...")
    
    # Upgrade to 13B model for better detail (given 40+ vRAM)
    model_id = "llava-hf/llava-1.5-13b-hf"
    
    # Load processor and model
    processor = AutoProcessor.from_pretrained(model_id)
    model = LlavaForConditionalGeneration.from_pretrained(
        model_id, 
        torch_dtype=torch.float16,
        low_cpu_mem_usage=True,
        device_map="auto"
    )

    # Clear prompt with an example for TOK man
    prompt_text = (
        "Describe the TOK man in this image in four detailed sentences. "
        "First sentence: style and type of the image (e.g., painting, photo). "
        "Second sentence: what the TOK man is doing. "
        "Third sentence: his appearance and specific details. "
        "Fourth sentence: composition, keywords separated by commas, precise layout. "
        "Example: 'The image is a digital painting. The TOK man is swinging a sword in a battle stance. He wears a futuristic silver suit with glowing blue stripes and a spiked helmet. The composition features dynamic lines, vibrant colors, action pose, dark stormy background.'"
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
    folder_path = '../images'
    
    # Check for 'rename' argument
    if len(sys.argv) > 1 and sys.argv[1] == "rename":
        rename_images(folder_path)
        print("Images renamed successfully.")
    else:
        # Always run rename first to ensure sequential naming
        print("Renaming images...")
        rename_images(folder_path)
        
    print("Generating captions...")
    generate_captions(folder_path)
