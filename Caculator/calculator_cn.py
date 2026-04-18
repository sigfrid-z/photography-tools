import tkinter as tk
from tkinter import ttk
import math

# --- Data Dictionaries ---
# Added "fl_range" (min, max) to dictate the slider limits dynamically based on sensor reality
SENSORS = {
    "中画幅 (哈苏 X2D)": {"w": 43.8, "h": 32.9, "cf": 0.79, "fl_range": (20.0, 300.0)},
    "全画幅": {"w": 36.0, "h": 24.0, "cf": 1.00, "fl_range": (10.0, 800.0)},
    "APS-C": {"w": 23.6, "h": 15.6, "cf": 1.52, "fl_range": (8.0, 600.0)},
    "M43": {"w": 17.3, "h": 13.0, "cf": 2.00, "fl_range": (7.0, 400.0)},
    "1/0.98 英寸 (手机 LYT-900)": {"w": 13.2, "h": 8.8, "cf": 2.73, "fl_range": (4.0, 100.0)},
    "1/1.28 英寸 (手机 IMX903)": {"w": 9.8, "h": 7.4, "cf": 3.67, "fl_range": (3.0, 35.0)},
    "1/1.4 英寸 (手机 HP9)": {"w": 8.4, "h": 6.3, "cf": 4.28, "fl_range": (3.0, 35.0)}
}

APERTURES = [1.0, 1.2, 1.4, 1.7, 1.8, 2.0, 2.4, 2.8, 4.0, 5.6, 8.0, 11.0, 16.0, 22.0]

SHUTTER_STR = ["30s", "15s", "8s", "4s", "2s", "1s", "1/2", "1/4", "1/8", "1/15", "1/30", 
               "1/60", "1/125", "1/250", "1/500", "1/1000", "1/2000", "1/4000", "1/8000"]
SHUTTER_VAL = [30, 15, 8, 4, 2, 1, 1/2, 1/4, 1/8, 1/15, 1/30, 
               1/60, 1/125, 1/250, 1/500, 1/1000, 1/2000, 1/4000, 1/8000]

ISOS = [50, 100, 200, 400, 800, 1600, 3200, 6400, 12800, 25600]

class PhotoCalculator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("摄影传感器与曝光计算器")
        self.geometry("550x750")
        self.configure(padx=20, pady=20)

        # Variables
        self.sensor_var = tk.StringVar(value="全画幅")
        self.fl_var = tk.DoubleVar(value=50.0)
        self.dist_var = tk.DoubleVar(value=2.0)
        self.aperture_idx = tk.IntVar(value=7) # Default f/2.8
        self.shutter_idx = tk.IntVar(value=10) # Default 1/30
        self.iso_idx = tk.IntVar(value=1)      # Default 100

        self.create_widgets()
        self.update_sensor_limits() # Initialize slider limits
        self.update_calculations()

    def create_widgets(self):
        row = 0
        
        # --- Sensor Selection ---
        tk.Label(self, text="传感器尺寸:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky="w", pady=5)
        sensor_dropdown = ttk.Combobox(self, textvariable=self.sensor_var, values=list(SENSORS.keys()), state="readonly", width=30)
        sensor_dropdown.grid(row=row, column=1, sticky="w")
        # Bind the sensor change to update the slider limits FIRST
        sensor_dropdown.bind("<<ComboboxSelected>>", self.update_sensor_limits)
        row += 1

        # --- Continuous Sliders ---
        # Focal Length
        tk.Label(self, text="实际焦距 (mm):", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky="w", pady=(10, 0))
        self.fl_label = tk.Label(self, text="50.0 mm")
        self.fl_label.grid(row=row, column=1, sticky="e", pady=(10, 0))
        row += 1
        
        # Added resolution=0.1 to allow fractional focal lengths for phones
        self.fl_scale = tk.Scale(self, variable=self.fl_var, orient="horizontal", showvalue=0, resolution=0.1, command=self.update_calculations)
        self.fl_scale.grid(row=row, column=0, columnspan=2, sticky="we")
        row += 1

        # NEW: Quick Prime Buttons (Full Frame Equivalents)
        btn_frame = tk.Frame(self)
        btn_frame.grid(row=row, column=0, columnspan=2, sticky="we", pady=(2, 10))
        tk.Label(btn_frame, text="快速等效定焦:", font=("Arial", 8, "italic")).pack(side="left", padx=(0, 5))
        
        for prime in [24, 35, 50, 85, 100, 135]:
            tk.Button(btn_frame, text=f"{prime}mm", font=("Arial", 8), 
                      command=lambda p=prime: self.set_equiv_prime(p)).pack(side="left", padx=2)
        row += 1

        # Subject Distance
        tk.Label(self, text="对焦距离 (米):", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky="w", pady=10)
        self.dist_label = tk.Label(self, text="2.0 m")
        self.dist_label.grid(row=row, column=1, sticky="e")
        row += 1
        tk.Scale(self, variable=self.dist_var, from_=0.5, to=50.0, resolution=0.5, orient="horizontal", 
                 showvalue=0, command=self.update_calculations).grid(row=row, column=0, columnspan=2, sticky="we")
        row += 1

        # --- Discrete Sliders ---
        # Aperture
        tk.Label(self, text="光圈 (f-stop):", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky="w", pady=10)
        self.aperture_label = tk.Label(self, text="f/2.8")
        self.aperture_label.grid(row=row, column=1, sticky="e")
        row += 1
        tk.Scale(self, variable=self.aperture_idx, from_=0, to=len(APERTURES)-1, orient="horizontal", 
                 showvalue=0, command=self.update_calculations).grid(row=row, column=0, columnspan=2, sticky="we")
        row += 1

        # Shutter Speed
        tk.Label(self, text="快门速度:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky="w", pady=10)
        self.shutter_label = tk.Label(self, text="1/30s")
        self.shutter_label.grid(row=row, column=1, sticky="e")
        row += 1
        tk.Scale(self, variable=self.shutter_idx, from_=0, to=len(SHUTTER_STR)-1, orient="horizontal", 
                 showvalue=0, command=self.update_calculations).grid(row=row, column=0, columnspan=2, sticky="we")
        row += 1

        # ISO
        tk.Label(self, text="ISO:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky="w", pady=10)
        self.iso_label = tk.Label(self, text="100")
        self.iso_label.grid(row=row, column=1, sticky="e")
        row += 1
        tk.Scale(self, variable=self.iso_idx, from_=0, to=len(ISOS)-1, orient="horizontal", 
                 showvalue=0, command=self.update_calculations).grid(row=row, column=0, columnspan=2, sticky="we")
        row += 1

        # --- Results Display ---
        ttk.Separator(self, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky="we", pady=15)
        row += 1

        self.results_text = tk.Text(self, height=12, width=50, state="disabled", font=("Courier", 10), bg="#f4f4f4")
        self.results_text.grid(row=row, column=0, columnspan=2, sticky="we")

    def set_equiv_prime(self, equiv_fl):
        sensor_key = self.sensor_var.get()
        cf = SENSORS[sensor_key]["cf"]
        
        # Calculate what the actual focal length needs to be to hit this FF equivalent
        actual_fl = equiv_fl / cf
        
        # Ensure it doesn't exceed the slider limits for the current sensor
        min_fl, max_fl = SENSORS[sensor_key]["fl_range"]
        actual_fl = max(min_fl, min(actual_fl, max_fl))
        
        # Set the slider value and trigger the update
        self.fl_var.set(actual_fl)
        self.update_calculations()

    def update_sensor_limits(self, event=None):
        # 1. Look up the min and max focal length for the selected sensor
        sensor_key = self.sensor_var.get()
        min_fl, max_fl = SENSORS[sensor_key]["fl_range"]
        
        # 2. Update the slider configuration
        self.fl_scale.config(from_=min_fl, to=max_fl)
        
        # 3. Prevent the current slider value from being out of the new bounds
        current_fl = self.fl_var.get()
        if current_fl < min_fl:
            self.fl_var.set(min_fl)
        elif current_fl > max_fl:
            self.fl_var.set(max_fl)
            
        # 4. Trigger calculations to update the display
        self.update_calculations()

    def update_calculations(self, *args):
        # 1. Fetch values
        sensor_key = self.sensor_var.get()
        cf = SENSORS[sensor_key]["cf"]
        fl = self.fl_var.get()
        dist_m = self.dist_var.get()
        dist_mm = dist_m * 1000
        
        aperture = APERTURES[self.aperture_idx.get()]
        shutter_s = SHUTTER_STR[self.shutter_idx.get()]
        shutter_v = SHUTTER_VAL[self.shutter_idx.get()]
        iso = ISOS[self.iso_idx.get()]

        # Update labels above sliders
        self.fl_label.config(text=f"{fl:.1f} mm")
        self.dist_label.config(text=f"{dist_m:.1f} m")
        self.aperture_label.config(text=f"f/{aperture}")
        self.shutter_label.config(text=f"{shutter_s}")
        self.iso_label.config(text=f"{iso}")

        # 2. Calculations
        # Equivalents
        eq_fl = fl * cf
        eq_aperture = aperture * cf
        
        # Exposure Value (EV)
        # EV at ISO 100: log2(N^2 / t)
        ev_100 = math.log2((aperture**2) / shutter_v)
        # Required Scene EV for the selected ISO
        ev_scene = ev_100 - math.log2(iso / 100)

        # Depth of Field (DoF)
        # Standard Circle of Confusion is roughly 0.030mm for Full Frame
        coc = 0.030 / cf 
        
        # Hyperfocal Distance: H = (f^2) / (N * c)
        hyperfocal_mm = (fl**2) / (aperture * coc)
        
        if dist_mm >= hyperfocal_mm:
            near_limit = (hyperfocal_mm * dist_mm) / (hyperfocal_mm + dist_mm)
            far_limit = float('inf')
        else:
            near_limit = (hyperfocal_mm * dist_mm) / (hyperfocal_mm + dist_mm)
            far_limit = (hyperfocal_mm * dist_mm) / (hyperfocal_mm - dist_mm)
        
        near_m = near_limit / 1000
        far_m = far_limit / 1000 if far_limit != float('inf') else float('inf')
        total_dof = (far_m - near_m) if far_m != float('inf') else float('inf')

        # 3. Format Output Text
        output =  f"--- 传感器等效数据 ---\n"
        output += f"全画幅等效焦距     : {eq_fl:.1f} mm\n"
        output += f"全画幅等效光圈     : f/{eq_aperture:.1f} (总进光量/景深)\n\n"
        
        output += f"--- 光线 / 曝光 ---\n"
        output += f"曝光值 (EV100)     : {ev_100:.2f} EV\n"
        output += f"所需场景亮度       : {ev_scene:.2f} EV\n"
        output += f"(EV值越低 = 场景越暗 / 收集光线越多)\n\n"
        
        output += f"--- 景深 ---\n"
        output += f"超焦距             : {hyperfocal_mm/1000:.2f} m\n"
        output += f"近点极限           : {near_m:.2f} m\n"
        
        if far_m == float('inf'):
            output += f"远点极限           : 无限远\n"
            output += f"总景深             : 无限远\n"
        else:
            output += f"远点极限           : {far_m:.2f} m\n"
            output += f"总景深             : {total_dof:.2f} m\n"

        self.results_text.config(state="normal")
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, output)
        self.results_text.config(state="disabled")

if __name__ == "__main__":
    app = PhotoCalculator()
    app.mainloop()