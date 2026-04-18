import numpy as np
from PIL import Image

def generate_hald(grid_size=32, output_filename="neutral_hald.png"):
    # Calculate dimensions: 8 blocks wide, 4 blocks high (8x4 = 32 blocks total)
    width = 8 * grid_size   # 256 pixels
    height = 4 * grid_size  # 128 pixels
    
    # Create an empty array for the image
    pixels = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Loop through Blue, Green, and Red to build the 3D color cube
    for b in range(grid_size):
        for g in range(grid_size):
            for r in range(grid_size):
                
                # Map 3D coordinates to 2D image coordinates
                x = (b % 8) * grid_size + r
                y = (b // 8) * grid_size + g
                
                # Scale the 0-31 grid values up to 0-255 pixel values mathematically
                r_val = int(round(r * 255.0 / (grid_size - 1)))
                g_val = int(round(g * 255.0 / (grid_size - 1)))
                b_val = int(round(b * 255.0 / (grid_size - 1)))
                
                pixels[y, x] = [r_val, g_val, b_val]
                
    # Save as a lossless PNG
    img = Image.fromarray(pixels, 'RGB')
    img.save(output_filename)
    print(f"Success! Created {output_filename} ({width}x{height})")

if __name__ == "__main__":
    generate_hald()