import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image
import os

class SocialMediaCollageTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Social Media Image Preparer")
        self.root.geometry("400x300")
        self.root.configure(padx=20, pady=20)

        self.file_paths = []

        # UI Elements
        tk.Label(root, text="Step 1: Select Images", font=("Arial", 12, "bold")).pack(pady=(0, 5))
        
        self.btn_select = tk.Button(root, text="Select 1 or 2 Photos", command=self.select_images)
        self.btn_select.pack(pady=5)

        self.lbl_selected = tk.Label(root, text="No images selected.", fg="gray")
        self.lbl_selected.pack(pady=(0, 15))

        tk.Label(root, text="Step 2: Choose Processing Mode", font=("Arial", 12, "bold")).pack(pady=(0, 5))

        self.btn_stack = tk.Button(root, text="Mode A: Stack Vertically (Requires 2 Photos)", 
                                   command=self.stack_vertically, state=tk.DISABLED)
        self.btn_stack.pack(pady=5, fill=tk.X)

        self.btn_slice = tk.Button(root, text="Mode B: Slice for Swipe Panorama (Requires 1 Photo)", 
                                   command=self.slice_panorama, state=tk.DISABLED)
        self.btn_slice.pack(pady=5, fill=tk.X)

    def select_images(self):
        files = filedialog.askopenfilenames(
            title="Select Photos",
            filetypes=[("Image files", "*.jpg *.jpeg *.png")]
        )
        
        if files:
            if len(files) > 2:
                messagebox.showwarning("Too Many Files", "Please select only 1 or 2 images.")
                return
            
            self.file_paths = list(files)
            self.lbl_selected.config(text=f"{len(self.file_paths)} image(s) selected.")
            
            # Update button states based on selection count
            self.btn_stack.config(state=tk.NORMAL if len(self.file_paths) == 2 else tk.DISABLED)
            self.btn_slice.config(state=tk.NORMAL if len(self.file_paths) == 1 else tk.DISABLED)

    def stack_vertically(self):
        try:
            img1 = Image.open(self.file_paths[0])
            img2 = Image.open(self.file_paths[1])

            # Resize img2 to match img1's width to ensure a clean stack
            if img1.width != img2.width:
                aspect_ratio = img2.height / img2.width
                new_height = int(img1.width * aspect_ratio)
                img2 = img2.resize((img1.width, new_height), Image.Resampling.LANCZOS)

            # Create a new blank image with combined height
            total_height = img1.height + img2.height
            new_image = Image.new('RGB', (img1.width, total_height))

            # Paste images into the blank canvas
            new_image.paste(img1, (0, 0))
            new_image.paste(img2, (0, img1.height))

            save_path = self.get_save_path("stacked_collage.jpg")
            if save_path:
                new_image.save(save_path, quality=95)
                messagebox.showinfo("Success", f"Stacked image saved to:\n{save_path}")
                
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred:\n{str(e)}")

    def slice_panorama(self):
        try:
            img = Image.open(self.file_paths[0])
            width, height = img.size

            # Calculate the middle point
            mid_point = width // 2

            # Crop into two halves (Left, Upper, Right, Lower)
            left_half = img.crop((0, 0, mid_point, height))
            right_half = img.crop((mid_point, 0, width, height))

            save_dir = filedialog.askdirectory(title="Select Folder to Save Slices")
            if save_dir:
                base_name = os.path.splitext(os.path.basename(self.file_paths[0]))[0]
                path1 = os.path.join(save_dir, f"{base_name}_part1.jpg")
                path2 = os.path.join(save_dir, f"{base_name}_part2.jpg")

                left_half.save(path1, quality=95)
                right_half.save(path2, quality=95)

                messagebox.showinfo("Success", f"Slices saved successfully in:\n{save_dir}")

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred:\n{str(e)}")

    def get_save_path(self, default_name):
        return filedialog.asksaveasfilename(
            defaultextension=".jpg",
            initialfile=default_name,
            filetypes=[("JPEG", "*.jpg"), ("PNG", "*.png")],
            title="Save Image As"
        )

if __name__ == "__main__":
    root = tk.Tk()
    app = SocialMediaCollageTool(root)
    root.mainloop()