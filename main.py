import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import random
from PIL import Image, ImageTk
from photogrid.image_utils import analyze_images, crop_to_aspect_ratio
from photogrid.layout import calculate_target_sizes, build_rows, justify_row

class PhotoGridApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Photo Grid Generator")
        self.geometry("1024x768")

        # App state
        self.folder_path = None
        self.all_images = []
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

        # Cropping Option
        crop_frame = ttk.LabelFrame(controls_frame, text="Cropping")
        crop_frame.pack(fill=tk.X, padx=5, pady=5)
        self.crop_var = tk.BooleanVar()
        self.crop_check = ttk.Checkbutton(crop_frame, text="Enable Smart Cropping", variable=self.crop_var)
        self.crop_check.pack(padx=5, pady=2, anchor="w")

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
        h, v = analyze_images(self.folder_path)
        self.all_images = h + v
        
        total_images = len(self.all_images)
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
            is_cropping = self.crop_var.get()
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid integers for dimensions and spacing.")
            return

        num_images = len(self.all_images)
        if num_images == 0:
            messagebox.showinfo("No Images", "No images to generate a layout from.")
            return

        random.shuffle(self.all_images)

        best_layout = None
        max_score = -float('inf')

        # New, smarter target scale calculation
        canvas_aspect_ratio = output_w / output_h
        avg_aspect_ratio = sum(img.aspect_ratio for img in self.all_images) / num_images if num_images > 0 else 1
        
        # Estimate num columns to guess a width-constrained size
        est_cols = (num_images * canvas_aspect_ratio / avg_aspect_ratio) ** 0.5
        est_cols = max(1, round(est_cols))
        
        # Estimate a target width based on this
        target_w = (output_w - (est_cols - 1) * min_space) / est_cols
        target_h = target_w / avg_aspect_ratio
        target_area = target_w * target_h
        target_scale = max(1, target_area ** 0.5)
        
        for i in range(50):
            scale = target_scale * (0.5 + (i / 49.0) * 2.5)
            if scale == 0: continue

            if is_cropping:
                target_aspect_ratio = output_w / output_h
                img_h = scale
                img_w = scale * target_aspect_ratio
                sized_images = [{'path': img.path, 'width': img_w, 'height': img_h} for img in self.all_images]
            else:
                h_imgs = [img for img in self.all_images if img.aspect_ratio > 1]
                v_imgs = [img for img in self.all_images if img.aspect_ratio < 1]
                sizer = calculate_target_sizes(h_imgs, v_imgs)
                w_h, h_h, w_v, h_v = sizer(scale)
                sized_images = [{'path': img.path, 'width': w_h if img.aspect_ratio > 1 else w_v, 'height': h_h if img.aspect_ratio > 1 else h_v} for img in self.all_images]

            rows_of_images = build_rows(sized_images, output_w, min_space)
            layout_w, layout_h, total_photo_area = self._calculate_layout_metrics(rows_of_images, min_space)

            if layout_w > output_w or layout_h > output_h:
                final_score = -1
            else:
                coverage_score = total_photo_area / (output_w * output_h)
                canvas_aspect_ratio = output_w / output_h
                layout_aspect_ratio = layout_w / layout_h if layout_h > 0 else 0
                balance_penalty = abs(canvas_aspect_ratio - layout_aspect_ratio) / canvas_aspect_ratio
                final_score = coverage_score - balance_penalty

            if final_score > max_score:
                max_score = final_score
                best_layout = self._construct_layout(rows_of_images, output_w, min_space, max_space)

        self.layout = best_layout
        self._update_preview()
        self.save_button.config(state="normal")
        
        final_photo_area = sum(img['width'] * img['height'] for img in best_layout) if best_layout else 0
        final_coverage = final_photo_area / (output_w * output_h)
        coverage_percent = final_coverage * 100

        if coverage_percent >= 80:
            messagebox.showinfo("Layout Generated", f"Coverage: {coverage_percent:.1f}%\nGoal of 80% was met.")
        else:
            messagebox.showwarning("Layout Generated", f"Coverage: {coverage_percent:.1f}%\nCould not achieve 80% coverage with the current settings.")

    def _calculate_layout_metrics(self, rows_of_images, min_space):
        layout_w = 0
        layout_h = 0
        total_photo_area = 0
        current_y = 0
        for row in rows_of_images:
            row_height = max(img['height'] for img in row)
            row_width = sum(img['width'] for img in row) + (len(row) - 1) * min_space if len(row) > 1 else sum(img['width'] for img in row)
            layout_w = max(layout_w, row_width)
            layout_h = current_y + row_height
            current_y += row_height + min_space
            total_photo_area += sum(img['width'] * img['height'] for img in row)
        return layout_w, layout_h, total_photo_area

    def _construct_layout(self, rows_of_images, output_w, min_space, max_space):
        final_layout = []
        current_y = 0
        for row in rows_of_images:
            row_height = max(img['height'] for img in row)
            justified_positions = justify_row(row, output_w, min_space, max_space)
            for pos_info in justified_positions:
                final_layout.append({
                    'path': pos_info['image']['path'],
                    'x': pos_info['x'], 'y': current_y,
                    'width': pos_info['image']['width'], 'height': pos_info['image']['height']
                })
            current_y += row_height + min_space
        return final_layout

    def _update_preview(self):
        if not self.layout:
            return

        self.update_idletasks()
        preview_w = self.preview_frame.winfo_width()
        preview_h = self.preview_frame.winfo_height()
        if preview_w < 2 or preview_h < 2: preview_w, preview_h = 800, 600

        output_w = int(self.width_entry.get())
        output_h = int(self.height_entry.get())
        is_cropping = self.crop_var.get()
        target_aspect_ratio = output_w / output_h

        preview_img = Image.new('RGB', (output_w, output_h), 'lightgrey')

        for img_layout in self.layout:
            with Image.open(img_layout['path']) as img:
                if is_cropping:
                    img = crop_to_aspect_ratio(img, target_aspect_ratio)
                img = img.resize((int(img_layout['width']), int(img_layout['height'])), Image.Resampling.LANCZOS)
                preview_img.paste(img, (int(img_layout['x']), int(img_layout['y'])))
        
        preview_img.thumbnail((preview_w - 20, preview_h - 20), Image.Resampling.LANCZOS)
        
        self.preview_image = ImageTk.PhotoImage(preview_img)
        self.preview_label.config(image=self.preview_image, text="")

    def save_image(self):
        if not self.layout:
            messagebox.showerror("Error", "No layout has been generated to save.")
            return

        save_path = filedialog.asksaveasfilename(defaultextension=".jpg", filetypes=[("JPEG Image", "*.jpg")], title="Save Collage As...")
        if not save_path: return

        output_w = int(self.width_entry.get())
        output_h = int(self.height_entry.get())
        is_cropping = self.crop_var.get()
        target_aspect_ratio = output_w / output_h
        
        final_image = Image.new('RGB', (output_w, output_h), 'white')

        for img_layout in self.layout:
            with Image.open(img_layout['path']) as img:
                if is_cropping:
                    img = crop_to_aspect_ratio(img, target_aspect_ratio)
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