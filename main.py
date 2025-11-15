import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import random
from PIL import Image, ImageTk
from photogrid.image_utils import analyze_images
from photogrid.layout import calculate_target_sizes, build_rows, justify_row

class PhotoGridApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Photo Grid Generator")
        self.geometry("1024x768")

        # App state
        self.folder_path = None
        self.horizontal_images = []
        self.vertical_images = []
        self.layout = None
        self.preview_image = None

        # --- Main Layout ---
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)

        # --- Controls Frame ---
        controls_frame = ttk.LabelFrame(main_frame, text="Controls")
        controls_frame.grid(column=0, row=0, padx=(0, 10), pady=5, sticky="ns")
        
        # Folder Selection
        folder_frame = ttk.Frame(controls_frame)
        folder_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(folder_frame, text="Select Image Folder...", command=self.select_folder).pack(fill=tk.X)
        self.folder_label = ttk.Label(folder_frame, text="No folder selected", wraplength=180)
        self.folder_label.pack(fill=tk.X, pady=(5,0))

        # Dimensions
        dims_frame = ttk.LabelFrame(controls_frame, text="Output Size")
        dims_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(dims_frame, text="Width:").grid(row=0, column=0, sticky="w")
        self.width_entry = ttk.Entry(dims_frame, width=8)
        self.width_entry.grid(row=0, column=1, padx=5)
        self.width_entry.insert(0, "1920")
        ttk.Label(dims_frame, text="Height:").grid(row=1, column=0, sticky="w")
        self.height_entry = ttk.Entry(dims_frame, width=8)
        self.height_entry.grid(row=1, column=1, padx=5)
        self.height_entry.insert(0, "1080")

        # Spacing
        space_frame = ttk.LabelFrame(controls_frame, text="Spacing (px)")
        space_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(space_frame, text="Min:").grid(row=0, column=0, sticky="w")
        self.min_space_entry = ttk.Entry(space_frame, width=6)
        self.min_space_entry.grid(row=0, column=1, padx=5)
        self.min_space_entry.insert(0, "10")
        ttk.Label(space_frame, text="Max:").grid(row=1, column=0, sticky="w")
        self.max_space_entry = ttk.Entry(space_frame, width=6)
        self.max_space_entry.grid(row=1, column=1, padx=5)
        self.max_space_entry.insert(0, "50")

        # Actions
        action_frame = ttk.Frame(controls_frame)
        action_frame.pack(fill=tk.X, padx=5, pady=10)
        self.generate_button = ttk.Button(action_frame, text="Generate / Shuffle Layout", state="disabled", command=self.generate_layout)
        self.generate_button.pack(fill=tk.X)
        self.save_button = ttk.Button(action_frame, text="Save Image...", state="disabled", command=self.save_image)
        self.save_button.pack(fill=tk.X, pady=(5,0))

        # --- Preview Frame ---
        self.preview_frame = ttk.LabelFrame(main_frame, text="Preview")
        self.preview_frame.grid(column=1, row=0, sticky="nsew")
        self.preview_frame.columnconfigure(0, weight=1)
        self.preview_frame.rowconfigure(0, weight=1)
        
        self.preview_label = ttk.Label(self.preview_frame, text="Select a folder and click 'Generate' to see a preview.")
        self.preview_label.grid(row=0, column=0, sticky="nsew")

    def select_folder(self):
        path = filedialog.askdirectory()
        if not path:
            return
        
        self.folder_path = path
        self.horizontal_images, self.vertical_images = analyze_images(self.folder_path)
        
        total_images = len(self.horizontal_images) + len(self.vertical_images)
        self.folder_label.config(text=f"Selected: {os.path.basename(self.folder_path)}\n({total_images} images found)")
        
        if total_images > 0:
            self.generate_button.config(state="normal")
        else:
            self.generate_button.config(state="disabled")
            messagebox.showinfo("No Images Found", "Could not find any compatible (horizontal/vertical) JPEG images in the selected folder.")

    def generate_layout(self):
        try:
            output_w = int(self.width_entry.get())
            output_h = int(self.height_entry.get())
            min_space = int(self.min_space_entry.get())
            max_space = int(self.max_space_entry.get())
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid integers for dimensions and spacing.")
            return

        if not self.horizontal_images and not self.vertical_images:
            messagebox.showinfo("No Images", "No images to generate a layout from.")
            return

        all_images = self.horizontal_images + self.vertical_images
        random.shuffle(all_images)
        num_images = len(all_images)
        if num_images == 0: return

        sizer = calculate_target_sizes(self.horizontal_images, self.vertical_images)

        # --- Search for the best scale to minimize wasted space ---
        best_layout = None
        min_cost = float('inf')

        # 1. Find a reasonable center-point for our search
        target_area_per_image = (output_w * output_h) / num_images
        target_scale = target_area_per_image ** 0.5
        
        # 2. Test a range of scales around that center-point
        for i in range(20):
            scale = target_scale * (0.5 + (i / 19.0) * 1.5) # Search from 50% to 200% of target
            if scale == 0: continue

            w_h, h_h, w_v, h_v = sizer(scale)

            sized_images = [{'path': img.path, 'width': w_h if img.aspect_ratio > 1 else w_v, 'height': h_h if img.aspect_ratio > 1 else h_v} for img in all_images]
            rows_of_images = build_rows(sized_images, output_w, min_space)

            # Calculate the total height of this potential layout
            total_height = 0
            num_v_gaps = len(rows_of_images) - 1
            if num_v_gaps > 0:
                # Estimate vertical spacing based on a "perfect fit"
                total_row_height = sum(max(img['height'] for img in row) for row in rows_of_images)
                v_spacing = (output_h - total_row_height) / num_v_gaps
                v_spacing = max(min_space, v_spacing)
                total_height = total_row_height + num_v_gaps * v_spacing
            elif rows_of_images:
                total_height = max(img['height'] for img in rows_of_images[0])

            # Cost is how far we are from the target height
            cost = abs(output_h - total_height)

            if cost < min_cost:
                min_cost = cost
                
                # Construct the full layout for this "best" scale
                final_layout = []
                current_y = 0
                
                # Recalculate final vertical spacing for the best layout
                total_row_height = sum(max(img['height'] for img in row) for row in rows_of_images)
                v_spacing = (output_h - total_row_height) / num_v_gaps if num_v_gaps > 0 else 0
                v_spacing = max(min_space, v_spacing)

                for row in rows_of_images:
                    row_height = max(img['height'] for img in row)
                    justified_positions = justify_row(row, output_w, min_space, max_space)
                    for pos_info in justified_positions:
                        final_layout.append({
                            'path': pos_info['image']['path'],
                            'x': pos_info['x'], 'y': current_y,
                            'width': pos_info['image']['width'], 'height': pos_info['image']['height']
                        })
                    current_y += row_height + v_spacing
                best_layout = final_layout

        self.layout = best_layout
        self._update_preview()
        self.save_button.config(state="normal")

    def _update_preview(self):
        if not self.layout:
            return

        # Get preview frame size
        self.update_idletasks()
        preview_w = self.preview_frame.winfo_width()
        preview_h = self.preview_frame.winfo_height()
        if preview_w < 2 or preview_h < 2: # Frame not rendered yet
            preview_w, preview_h = 800, 600

        output_w = int(self.width_entry.get())
        output_h = int(self.height_entry.get())

        # Create a blank image for the preview
        preview_img = Image.new('RGB', (output_w, output_h), 'lightgrey')

        for img_layout in self.layout:
            with Image.open(img_layout['path']) as img:
                img = img.resize((int(img_layout['width']), int(img_layout['height'])), Image.Resampling.LANCZOS)
                preview_img.paste(img, (int(img_layout['x']), int(img_layout['y'])))
        
        # Scale final preview to fit the UI
        preview_img.thumbnail((preview_w - 20, preview_h - 20), Image.Resampling.LANCZOS)
        
        self.preview_image = ImageTk.PhotoImage(preview_img)
        self.preview_label.config(image=self.preview_image, text="")

    def save_image(self):
        if not self.layout:
            messagebox.showerror("Error", "No layout has been generated to save.")
            return

        save_path = filedialog.asksaveasfilename(
            defaultextension=".jpg",
            filetypes=[("JPEG Image", "*.jpg"), ("PNG Image", "*.png"), ("All Files", "*.*")],
            title="Save Collage As..."
        )
        if not save_path:
            return

        output_w = int(self.width_entry.get())
        output_h = int(self.height_entry.get())
        
        final_image = Image.new('RGB', (output_w, output_h), 'white')

        for img_layout in self.layout:
            with Image.open(img_layout['path']) as img:
                img = img.resize((int(img_layout['width']), int(img_layout['height'])), Image.Resampling.LANCZOS)
                final_image.paste(img, (int(img_layout['x']), int(img_layout['y'])))
        
        try:
            final_image.save(save_path)
            messagebox.showinfo("Success", f"Image saved successfully to:\n{save_path}")
        except Exception as e:
            messagebox.showerror("Save Error", f"Could not save the image.\nError: {e}")


if __name__ == "__main__":
    app = PhotoGridApp()
    app.mainloop()
