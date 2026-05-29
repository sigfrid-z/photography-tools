import os
import shutil
from datetime import datetime
from PIL import Image

# ==========================================
# CONFIGURATION (Hardcode your details here)
# ==========================================

# List all the folders containing the duplicate/messy files
SOURCE_FOLDERS = [
    r"D:\Pictures\TrocaderoP2\DxO_Exports",
    r"D:\Pictures\180526Trocadero\DxO_Exports"
]

# The folder where the newly renamed files will go
# (The script will create this if it doesn't exist)
DESTINATION_FOLDER = r"D:\Trocadero_Sorted"

# The sequence number to start at (e.g., 10000 for DSC10000_DxO.jpg)
START_NUMBER = 10000

# The naming template. {05d} ensures the number is padded with zeros to 5 digits.
FILENAME_TEMPLATE = "DSC{number:05d}_DxO.jpg"

# ==========================================

def get_exif_datetime(filepath):
    """
    Extracts the 'DateTimeOriginal' from the image EXIF data.
    Falls back to the file's OS modification time if EXIF is missing/corrupted.
    """
    try:
        image = Image.open(filepath)
        exifdata = image.getexif()
        
        # 36867 is the standard EXIF tag for DateTimeOriginal
        if exifdata and 36867 in exifdata:
            date_str = exifdata[36867]
            # EXIF date format is standard: YYYY:MM:DD HH:MM:SS
            return datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
    except Exception as e:
        print(f"Warning: Could not read EXIF for {filepath}. Using file modification time. ({e})")
        pass
    
    # Fallback if EXIF reading fails or tag is missing
    return datetime.fromtimestamp(os.path.getmtime(filepath))

def main():
    print("Gathering files...")
    all_files = []
    
    # 1. Collect all JPG files from the source directories
    for folder in SOURCE_FOLDERS:
        if not os.path.exists(folder):
            print(f"Skipping {folder} - Directory does not exist.")
            continue
            
        for filename in os.listdir(folder):
            if filename.lower().endswith(('.jpg', '.jpeg')):
                all_files.append(os.path.join(folder, filename))

    if not all_files:
        print("No JPG files found in the source directories. Exiting.")
        return

    print(f"Found {len(all_files)} images. Reading EXIF data...")
    
    # 2. Extract datetime for each file
    files_with_dates = []
    for filepath in all_files:
        dt = get_exif_datetime(filepath)
        files_with_dates.append((dt, filepath))

    # 3. Sort chronologically based on the extracted datetime
    print("Sorting files chronologically...")
    files_with_dates.sort(key=lambda x: x[0])

    # 4. Create destination directory if it doesn't exist
    os.makedirs(DESTINATION_FOLDER, exist_ok=True)

    # 5. Copy and rename
    print("Starting the copy and rename process...")
    current_number = START_NUMBER
    
    for dt, original_path in files_with_dates:
        new_filename = FILENAME_TEMPLATE.format(number=current_number)
        new_filepath = os.path.join(DESTINATION_FOLDER, new_filename)
        
        # shutil.copy2 preserves original file metadata (like creation time) during the copy
        shutil.copy2(original_path, new_filepath)
        print(f"Copied: {os.path.basename(original_path)} --> {new_filename} (Shot at: {dt})")
        
        current_number += 1

    print("\nProcess complete! All files have been safely copied and renamed.")

if __name__ == "__main__":
    main()