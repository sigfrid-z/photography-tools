import os
import numpy as np
from PIL import Image

def batch_convert_to_cube(input_folder, output_folder, grid_size=32):
    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    
    # Find all images in the input folder
    valid_extensions = ('.tif', '.tiff', '.png')
    files_to_process = [f for f in os.listdir(input_folder) if f.lower().endswith(valid_extensions)]
    
    if not files_to_process:
        print(f"No valid images ({valid_extensions}) found in '{input_folder}'.")
        return

    for filename in files_to_process:
        filepath = os.path.join(input_folder, filename)
        preset_name = os.path.splitext(filename)[0]
        output_filepath = os.path.join(output_folder, f"{preset_name}.cube")
        
        try:
            # Load image and convert to float values between 0.0 and 1.0
            img = Image.open(filepath).convert('RGB')
            pixels = np.array(img, dtype=np.float32) / 255.0
            
            with open(output_filepath, 'w') as f:
                # Write .cube header
                f.write(f"TITLE \"{preset_name}\"\n")
                f.write(f"LUT_3D_SIZE {grid_size}\n\n")
                
                # Reverse the exact same math from the generator
                for b in range(grid_size):
                    for g in range(grid_size):
                        for r in range(grid_size):
                            x = (b % 8) * grid_size + r
                            y = (b // 8) * grid_size + g
                            
                            # Grab the new color and clamp it to ensure it stays within 0.0 - 1.0
                            color = pixels[y, x]
                            r_val = max(0.0, min(1.0, float(color[0])))
                            g_val = max(0.0, min(1.0, float(color[1])))
                            b_val = max(0.0, min(1.0, float(color[2])))
                            
                            # Write RGB values to the cube file
                            f.write(f"{r_val:.6f} {g_val:.6f} {b_val:.6f}\n")
                            
            print(f"Converted: {filename} -> {preset_name}.cube")
            
        except Exception as e:
            print(f"Error processing {filename}: {e}")

if __name__ == "__main__":
    # Define your folders here
    INPUT_DIR = "processed_tifs"
    OUTPUT_DIR = "output_luts"
    
    batch_convert_to_cube(INPUT_DIR, OUTPUT_DIR)