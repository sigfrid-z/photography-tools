import os
import shutil
import json
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import exifread
try:
    from openpyxl import Workbook
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

class PhotoOrganizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("DxO Photo Organizer")
        self.root.geometry("500x350")
        self.root.config(padx=20, pady=20)

        self.folder_path = tk.StringVar()
        self.report_format = tk.StringVar(value="JSON")
        
        # Subfolder names
        self.orig_folder_name = "Original_JPEGs"
        self.dxo_folder_name = "DxO_Exports"

        self.setup_ui()

    def setup_ui(self):
        # Folder Selection
        tk.Label(self.root, text="Target Folder:").pack(anchor="w")
        folder_frame = tk.Frame(self.root)
        folder_frame.pack(fill="x", pady=(0, 15))
        
        tk.Entry(folder_frame, textvariable=self.folder_path, width=45).pack(side="left", padx=(0, 10))
        tk.Button(folder_frame, text="Browse", command=self.browse_folder).pack(side="left")

        # Action Buttons
        tk.Label(self.root, text="Actions:", font=("Arial", 10, "bold")).pack(anchor="w", pady=(10, 5))
        
        tk.Button(self.root, text="1. Move Original Camera JPGs", width=35, command=self.move_original_jpgs).pack(pady=5)
        tk.Button(self.root, text="2. Move DxO Exported JPGs", width=35, command=self.move_dxo_jpgs).pack(pady=5)

        # Report Generation Section
        report_frame = tk.Frame(self.root)
        report_frame.pack(fill="x", pady=(20, 5))
        
        tk.Label(report_frame, text="Unedited RAWs Report Format:").pack(side="left")
        tk.Radiobutton(report_frame, text="JSON", variable=self.report_format, value="JSON").pack(side="left", padx=5)
        tk.Radiobutton(report_frame, text="Excel (.xlsx)", variable=self.report_format, value="XLSX", state="normal" if HAS_OPENPYXL else "disabled").pack(side="left")

        tk.Button(self.root, text="3. Generate Unedited RAWs Report", width=35, command=self.generate_report).pack(pady=10)

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_path.set(folder)

    def get_valid_folder(self):
        folder = self.folder_path.get()
        if not folder or not os.path.isdir(folder):
            messagebox.showerror("Error", "Please select a valid folder first.")
            return None
        return folder

    def move_original_jpgs(self):
        folder = self.get_valid_folder()
        if not folder: return

        target_dir = os.path.join(folder, self.orig_folder_name)
        os.makedirs(target_dir, exist_ok=True)

        moved_count = 0
        for filename in os.listdir(folder):
            # Check if it's a JPG and NOT a DxO export
            if filename.lower().endswith(('.jpg', '.jpeg')) and "_DxO" not in filename:
                src = os.path.join(folder, filename)
                dst = os.path.join(target_dir, filename)
                shutil.move(src, dst)
                moved_count += 1
                
        messagebox.showinfo("Success", f"Moved {moved_count} original JPGs to '{self.orig_folder_name}'.")

    def move_dxo_jpgs(self):
        folder = self.get_valid_folder()
        if not folder: return

        target_dir = os.path.join(folder, self.dxo_folder_name)
        os.makedirs(target_dir, exist_ok=True)

        moved_count = 0
        for filename in os.listdir(folder):
            # Check if it's a DxO export
            if filename.lower().endswith('.jpg') and "_DxO" in filename:
                src = os.path.join(folder, filename)
                dst = os.path.join(target_dir, filename)
                shutil.move(src, dst)
                moved_count += 1
                
        messagebox.showinfo("Success", f"Moved {moved_count} DxO JPGs to '{self.dxo_folder_name}'.")

    def extract_metadata(self, filepath):
        metadata = {
            "File Name": os.path.basename(filepath),
            "Date Taken": "N/A",
            "Camera": "N/A",
            "Lens": "N/A"
        }
        try:
            with open(filepath, 'rb') as f:
                tags = exifread.process_file(f, details=False)
                if "EXIF DateTimeOriginal" in tags:
                    metadata["Date Taken"] = str(tags["EXIF DateTimeOriginal"])
                if "Image Model" in tags:
                    metadata["Camera"] = str(tags["Image Model"])
                if "EXIF LensModel" in tags:
                    metadata["Lens"] = str(tags["EXIF LensModel"])
        except Exception:
            pass # Silently fail on individual file read errors
        return metadata

    def generate_report(self):
        folder = self.get_valid_folder()
        if not folder: return

        dxo_folder = os.path.join(folder, self.dxo_folder_name)
        
        # Get all ARW files in the main directory
        arw_files = [f for f in os.listdir(folder) if f.lower().endswith('.arw')]
        
        # Get all DxO exported JPGs (either in main folder or the moved subfolder)
        dxo_exports = []
        if os.path.exists(dxo_folder):
            dxo_exports.extend([f for f in os.listdir(dxo_folder) if "_DxO" in f])
        dxo_exports.extend([f for f in os.listdir(folder) if "_DxO" in f]) # Check main folder just in case
        
        unedited_data = []

        for arw in arw_files:
            # Assume DxO output looks like "DSC09641_DxO.jpg"
            base_name = os.path.splitext(arw)[0] 
            
            # Check if a file starting with the base name and containing _DxO exists
            is_edited = any(export.startswith(base_name) for export in dxo_exports)
            
            if not is_edited:
                filepath = os.path.join(folder, arw)
                meta = self.extract_metadata(filepath)
                unedited_data.append(meta)

        if not unedited_data:
            messagebox.showinfo("Report", "All ARW files seem to have a corresponding DxO export!")
            return

        # Save Report
        report_type = self.report_format.get()
        try:
            if report_type == "JSON":
                report_path = os.path.join(folder, "unedited_raws_report.json")
                with open(report_path, 'w') as f:
                    json.dump(unedited_data, f, indent=4)
                messagebox.showinfo("Success", f"Saved JSON report with {len(unedited_data)} files to:\n{report_path}")

            elif report_type == "XLSX":
                report_path = os.path.join(folder, "unedited_raws_report.xlsx")
                wb = Workbook()
                ws = wb.active
                ws.title = "Unedited RAWs"
                
                # Headers
                headers = list(unedited_data[0].keys())
                ws.append(headers)
                
                # Data
                for item in unedited_data:
                    ws.append([item[h] for h in headers])
                    
                wb.save(report_path)
                messagebox.showinfo("Success", f"Saved Excel report with {len(unedited_data)} files to:\n{report_path}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save report: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = PhotoOrganizerApp(root)
    root.mainloop()