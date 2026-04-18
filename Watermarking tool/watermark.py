import PIL.Image
import PIL.ExifTags
import PIL.ImageDraw
import PIL.ImageFont
import PIL.ImageOps
from fractions import Fraction
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# --- Configuration ---
# Standard fonts
try:
    FONT_PATH_BOLD = "arialbd.ttf"
    FONT_PATH_REG = "arial.ttf"
    # Test load to ensure they exist on system
    PIL.ImageFont.truetype(FONT_PATH_BOLD, 10)
except OSError:
    # Fallbacks for Mac/Linux
    try:
        FONT_PATH_BOLD = "/System/Library/Fonts/HelveticaNeue-Bold.otf"
        FONT_PATH_REG = "/System/Library/Fonts/HelveticaNeue.otf"
        PIL.ImageFont.truetype(FONT_PATH_BOLD, 10)
    except OSError:
        FONT_PATH_BOLD = "DejaVuSans-Bold.ttf"
        FONT_PATH_REG = "DejaVuSans.ttf"

BORDER_COLOR = (255, 255, 255)
TEXT_COLOR = (30, 30, 30)
BORDER_RATIO = 0.12
LOGO_PATH = None 

# --- Helper Functions for EXIF ---

def get_float(v):
    """Robustly converts EXIF values (tuples, Fractions, IFDRational) to float."""
    if v is None:
        return 0.0
    try:
        # Try direct float conversion (works for int, float, IFDRational)
        return float(v)
    except (TypeError, ValueError):
        # Handle tuple format (numerator, denominator)
        if isinstance(v, tuple) and len(v) == 2:
            if v[1] == 0: return 0.0
            return float(v[0]) / float(v[1])
        return 0.0

def format_shutter_speed(v):
    """Formats shutter speed (e.g., 0.01 -> 1/100s)."""
    val = get_float(v)
    if val <= 0: return ""
    if val >= 0.4: # For long exposures (0.4s and longer), show as decimal
        return f"{val}s"
    else:
        # Use Fraction to find the nearest rational number format (e.g. 1/100)
        f = Fraction(val).limit_denominator(8000)
        return f"{f.numerator}/{f.denominator}s"

def format_f_number(v):
    """Formats aperture (e.g., 6.3 -> f/6.3). Fixes the f/63/10 bug."""
    val = get_float(v)
    if val <= 0: return ""
    return f"f/{val:.1f}" if val % 1 else f"f/{int(val)}"

def format_gps(gps_info):
    """Formats GPSInfo dictionary into a readable string."""
    if not gps_info: return ""
    
    def to_deg(value, ref):
        try:
            d = get_float(value[0])
            m = get_float(value[1])
            s = get_float(value[2])
            return f"{int(d)}°{int(m)}'{int(s)}\"{ref}"
        except: return ""

    try:
        lat = to_deg(gps_info.get(2), gps_info.get(1))
        lon = to_deg(gps_info.get(4), gps_info.get(3))
        if lat and lon:
            return f"{lat} {lon}"
        return ""
    except:
        return ""

def extract_exif(image, manual_lens_name=""):
    """Extracts relevant EXIF data."""
    exif = image.getexif()
    exif_data = {}

    if exif:
        for tag_id, value in exif.items():
            tag_name = PIL.ExifTags.TAGS.get(tag_id, tag_id)
            exif_data[tag_name] = value

        # SubIFD for Exposure, ISO, F-Stop
        try:
            sub_ifd = exif.get_ifd(0x8769) 
            for tag_id, value in sub_ifd.items():
                tag_name = PIL.ExifTags.TAGS.get(tag_id, tag_id)
                exif_data[tag_name] = value
        except KeyError: pass

    # --- Parsing ---
    make = str(exif_data.get('Make', '')).strip()
    model = str(exif_data.get('Model', '')).strip()
    
    if make.lower() in model.lower():
         camera_name = model
    else:
         camera_name = f"{make} {model}".strip()
    if not camera_name: camera_name = "Unknown Camera"

    date_time = str(exif_data.get('DateTimeOriginal', exif_data.get('DateTime', '')))
    if len(date_time) > 16:
        date_time = date_time[:16].replace(':', '.')

    focal = get_float(exif_data.get('FocalLength'))
    focal_str = f"{int(round(focal))}mm" if focal > 0 else ""
    
    f_num_str = format_f_number(exif_data.get('FNumber'))
    shut_str = format_shutter_speed(exif_data.get('ExposureTime'))
    
    iso_val = exif_data.get('ISOSpeedRatings')
    if isinstance(iso_val, tuple): iso_val = iso_val[0]
    iso_str = f"ISO{iso_val}" if iso_val else ""

    # Lens Model detection
    lens_exif = str(exif_data.get('LensModel', '') or exif_data.get(0xA434, '')).strip()
    if len(lens_exif) < 3: lens_exif = ""
    
    # --- CHANGE: Separate Lens and Tech Strings ---
    lens_string = lens_exif if lens_exif else manual_lens_name

    tech_parts = []
    # Note: We do NOT add the lens here anymore
    if focal_str: tech_parts.append(focal_str)
    if f_num_str: tech_parts.append(f_num_str)
    if shut_str: tech_parts.append(shut_str)
    if iso_str: tech_parts.append(iso_str)
    
    tech_string = " ".join(tech_parts)

    return {
        'camera_name': camera_name,
        'date_time': date_time,
        'lens_string': lens_string,  # New Key
        'tech_string': tech_string
    }

def process_image(input_path, output_path, manual_lens=""):
    try:
        img = PIL.Image.open(input_path)
        img = PIL.ImageOps.exif_transpose(img)
    except Exception as e:
        return f"Error opening: {e}"

    exif_info = extract_exif(img, manual_lens)
    
    w, h = img.size
    is_portrait = h > w
    short_side = min(w, h)
    border_size = int(short_side * BORDER_RATIO)
    
    # Font scaling
    font_size_bold = int(border_size * 0.22)
    font_size_reg = int(border_size * 0.15)
    padding = int(border_size * 0.15)

    try:
        font_bold = PIL.ImageFont.truetype(FONT_PATH_BOLD, font_size_bold)
        font_reg = PIL.ImageFont.truetype(FONT_PATH_REG, font_size_reg)
    except:
        font_bold = PIL.ImageFont.load_default()
        font_reg = PIL.ImageFont.load_default()

    # --- CHANGE: Assign Text to Positions ---
    # Left Side
    text_left_top = exif_info['camera_name']
    text_left_bot = exif_info['date_time']
    
    # Right Side (Split into Lens on Top, Specs on Bottom)
    text_right_top = exif_info['lens_string']
    text_right_bot = exif_info['tech_string']

    # Canvas
    if is_portrait:
        # Vertical Layout (Right Border)
        new_w, new_h = w + border_size, h
        canvas = PIL.Image.new('RGB', (new_w, new_h), BORDER_COLOR)
        canvas.paste(img, (0, 0))
        draw = PIL.ImageDraw.Draw(canvas)
        
        # Top Block (Camera + Date)
        x_pos = w + padding
        y_top = padding * 2
        
        draw.text((x_pos, y_top), text_left_top, font=font_bold, fill=TEXT_COLOR, anchor="la")
        bbox = draw.textbbox((x_pos, y_top), text_left_top, font=font_bold, anchor="la")
        y_top += (bbox[3] - bbox[1]) + int(padding/2)
        draw.text((x_pos, y_top), text_left_bot, font=font_reg, fill=TEXT_COLOR, anchor="la")
        
        # Bottom Block (Lens + Tech Specs)
        y_bot = h - padding * 2
        
        # Draw Tech Specs (Bottom line of the block)
        draw.text((x_pos, y_bot), text_right_bot, font=font_reg, fill=TEXT_COLOR, anchor="ld")
        
        # Draw Lens Name (Top line of the block)
        if text_right_bot:
             bbox = draw.textbbox((x_pos, y_bot), text_right_bot, font=font_reg, anchor="ld")
             y_bot -= (bbox[3] - bbox[1]) + int(padding/2)
        
        draw.text((x_pos, y_bot), text_right_top, font=font_bold, fill=TEXT_COLOR, anchor="ld")

    else:
        # Horizontal Layout (Bottom Border)
        new_w, new_h = w, h + border_size
        canvas = PIL.Image.new('RGB', (new_w, new_h), BORDER_COLOR)
        canvas.paste(img, (0, 0))
        draw = PIL.ImageDraw.Draw(canvas)

        border_center_y = h + (border_size // 2)
        x_left = padding * 2
        x_right = w - padding * 2
        
        # Left Side: Camera Name (Top), Date (Bottom)
        draw.text((x_left, border_center_y), text_left_top, font=font_bold, fill=TEXT_COLOR, anchor="ls")
        draw.text((x_left, border_center_y + int(padding/2)), text_left_bot, font=font_reg, fill=TEXT_COLOR, anchor="la")

        # Right Side: Lens Name (Top), Tech Specs (Bottom)
        # Note: We anchor Tech Specs 'ra' (Right Ascender) or 'rt' to sit below the centerline?
        # Let's mirror the left side: 
        #   Lens Name -> anchor="rs" (Right Baseline, sits ON the center line)
        #   Tech Specs -> anchor="ra" (Right Ascender, sits BELOW the center line)
        
        draw.text((x_right, border_center_y), text_right_top, font=font_bold, fill=TEXT_COLOR, anchor="rs")
        draw.text((x_right, border_center_y + int(padding/2)), text_right_bot, font=font_reg, fill=TEXT_COLOR, anchor="ra")

    # Logo (Optional)
    if LOGO_PATH and os.path.exists(LOGO_PATH):
        try:
            logo = PIL.Image.open(LOGO_PATH).convert("RGBA")
            target_h = int(border_size * 0.5)
            aspect = logo.width / logo.height
            target_w = int(target_h * aspect)
            logo = logo.resize((target_w, target_h), PIL.Image.Resampling.LANCZOS)
            
            if is_portrait:
                logo_x = int(w + (border_size - target_w)/2)
                logo_y = int(h/2 - target_h/2)
            else:
                logo_x = int(w/2 - target_w/2)
                logo_y = int(h + (border_size - target_h)/2)

            canvas.paste(logo, (logo_x, logo_y), logo)
        except: pass

    canvas.save(output_path, quality=95)
    return "Success"

# --- GUI Application ---

class WatermarkApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Photo Watermarker")
        self.root.geometry("500x350")
        
        self.files = []

        # UI Elements
        frame = tk.Frame(root, padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)

        # 1. File Selection
        lbl_instr = tk.Label(frame, text="1. Select Photos (Batch)", font=("Arial", 10, "bold"))
        lbl_instr.pack(anchor="w")
        
        self.btn_select = tk.Button(frame, text="Choose Images...", command=self.select_files)
        self.btn_select.pack(anchor="w", pady=5)
        
        self.lbl_files = tk.Label(frame, text="No files selected", fg="gray")
        self.lbl_files.pack(anchor="w")

        tk.Frame(frame, height=15).pack() # Spacer

        # 2. Lens Fallback
        lbl_lens = tk.Label(frame, text="2. Lens Name (Fallback if EXIF missing)", font=("Arial", 10, "bold"))
        lbl_lens.pack(anchor="w")
        
        self.entry_lens = tk.Entry(frame, width=40)
        self.entry_lens.pack(anchor="w", pady=5)
        self.entry_lens.insert(0, "") # Default empty

        tk.Frame(frame, height=15).pack() # Spacer

        # 3. Process
        self.btn_run = tk.Button(frame, text="3. Process Images", command=self.run_process, bg="#dddddd", height=2)
        self.btn_run.pack(fill=tk.X, pady=10)
        
        self.progress = ttk.Progressbar(frame, orient=tk.HORIZONTAL, mode='determinate')
        self.progress.pack(fill=tk.X)
        
        self.lbl_status = tk.Label(frame, text="Ready")
        self.lbl_status.pack(pady=5)

    def select_files(self):
        filetypes = (("Images", "*.jpg *.jpeg *.png *.tif *.tiff"), ("All files", "*.*"))
        files = filedialog.askopenfilenames(title="Select photos", filetypes=filetypes)
        if files:
            self.files = files
            self.lbl_files.config(text=f"{len(files)} files selected", fg="black")

    def run_process(self):
        if not self.files:
            messagebox.showwarning("No Files", "Please select images first.")
            return

        manual_lens = self.entry_lens.get().strip()
        count = 0
        self.progress["maximum"] = len(self.files)
        
        for i, input_path in enumerate(self.files):
            # Generate output path (e.g., photo.jpg -> photo_marked.jpg)
            dir_name, file_name = os.path.split(input_path)
            name, ext = os.path.splitext(file_name)
            output_path = os.path.join(dir_name, f"{name}_marked{ext}")

            # Update status
            self.lbl_status.config(text=f"Processing: {file_name}...")
            self.root.update_idletasks()

            res = process_image(input_path, output_path, manual_lens)
            if res == "Success":
                count += 1
            
            self.progress["value"] = i + 1
        
        self.lbl_status.config(text=f"Done! Processed {count}/{len(self.files)} images.")
        messagebox.showinfo("Complete", f"Finished processing {count} images.")

if __name__ == "__main__":
    root = tk.Tk()
    app = WatermarkApp(root)
    root.mainloop()