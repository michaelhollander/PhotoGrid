### **Project Plan: Photo Grid Generator**

This plan outlines the implementation of a Python-based desktop application for creating photo collages from a folder of images. The final grid will be fully justified, meaning the content will stretch to fill the specified output dimensions by adjusting the spacing between images.

---

### **1. Core Technology Choices**

*   **Programming Language:** Python 3.
*   **GUI Framework:** `Tkinter`. It is included with standard Python installations, making the application easy to distribute and run without complex dependencies. It is fully capable of handling the required UI elements.
*   **Image Processing:** `Pillow` (the Python Imaging Library fork). This is the industry standard for image manipulation in Python. It will be used for opening, resizing, and compositing the images.

---

### **2. Phase 1: Backend Logic & Layout Algorithm**

This phase focuses on the core functionality without a graphical interface. The goal is to create a Python class or module that can take a list of image paths and configuration options and produce a final grid image.

1.  **Image Analysis:**
    *   Create a function that accepts a folder path.
    *   Iterate through the files, identifying all JPEGs.
    *   For each image, use `Pillow` to open it and record its width and height.
    *   Categorize images into two lists: `horizontal_images` and `vertical_images` based on their aspect ratio.

2.  **Sizing Calculation (The Core Constraint):**
    *   This is the most complex part. We need to determine the dimensions for horizontal and vertical images (`(w_h, h_h)` and `(w_v, h_v)`) that satisfy the user's rules.
    *   First, calculate the *average* aspect ratio for all horizontal images (`avg_ar_h`) and all vertical images (`avg_ar_v`).
    *   The constraints are:
        1.  `w_h / h_h = avg_ar_h` (Aspect ratio for horizontal images is preserved).
        2.  `w_v / h_v = avg_ar_v` (Aspect ratio for vertical images is preserved).
        3.  `w_h * h_h = w_v * h_v` (Area is equal).
    *   This system of equations can be solved. We can express all four dimension variables in terms of a single scaling factor. This factor will be determined by the layout algorithm to best fit the output canvas.

3.  **Layout Generation (The "Packing" and "Justification" Algorithm):**
    *   A greedy, row-based approach will be used to achieve justification.
    *   **Function Signature:** `generate_layout(images, output_width, output_height, min_spacing, max_spacing)`
    *   **Shuffle:** The function will begin by randomly shuffling the master list of all images. This is the key to the "Shuffle" feature.
    *   **Row-Based Placement Logic:**
        *   The algorithm will build the grid row by row. It will add images to a `current_row` list as long as their combined width plus the `min_spacing` does not exceed the `output_width`.
        *   When the next image in the shuffled list does not fit, the `current_row` is considered complete.
        *   **Horizontal Justification:**
            *   Calculate the `leftover_space` for the completed row.
            *   If the row has more than one image, this `leftover_space` is distributed evenly into the gaps between the images.
            *   The algorithm will check if the calculated spacing exceeds the user-defined `max_spacing`. If it does, the spacing will be capped at `max_spacing`, and the row will not be fully justified.
            *   The final positions of images in the row are calculated based on this new, adjusted spacing.
        *   Start a new row and repeat the process until all images are placed.
    *   **Vertical Justification:** After all rows are laid out, the total height of the content (all rows and the spacing between them) will likely not match the target `output_height`. To fix this, the entire grid (including all image heights and vertical gaps) will be scaled proportionally to fit the `output_height` perfectly. This ensures the grid is justified on all four sides.
    *   **Density & Variety:** The algorithm will try several base scaling factors for the image sizes. For each factor, it will run the placement logic and calculate the "waste" (e.g., how much the `max_spacing` was exceeded or how distorted the final vertical scaling is). It will then choose the scaling factor that results in the best layout.

4.  **Image Composition:**
    *   Create a function `save_image(layout, output_path)`.
    *   Use `Pillow` to create a new blank RGB image with the user-specified output dimensions and a white or black background.
    *   Iterate through the generated `layout`, which contains the path and final size/position for each image.
    *   For each image:
        *   Open the original file.
        *   Resize it to its calculated dimensions using `Pillow`'s high-quality downsampling filter (`Image.LANCZOS`).
        *   Paste the resized image onto the blank canvas at its designated `(x, y)` position.
    *   Save the final composite image to the specified output path.

---

### **3. Phase 2: GUI Development & Integration**

This phase involves building the `Tkinter` interface and connecting its controls to the backend logic.

1.  **Main Window Setup:**
    *   Create the main application window.
    *   Divide the window into two main frames: a `controls_frame` on the left or top, and a `preview_frame` for the image.

2.  **UI Controls (in `controls_frame`):**
    *   **Folder Selection:** A `Button` labeled "Select Image Folder". On click, it will use `tkinter.filedialog.askdirectory()` to get the folder path. A `Label` will display the selected path.
    *   **Output Dimensions:** Two `Entry` widgets with `Label`s: "Output Width" and "Output Height".
    *   **Spacing:** Two `Entry` widgets with `Label`s: "Min Spacing (pixels)" and "Max Spacing (pixels)".
    *   **Action Buttons:**
        *   A `Button` labeled "Generate / Shuffle Layout".
        *   A `Button` labeled "Save Image". This will be disabled until a layout is generated.

3.  **Image Preview (in `preview_frame`):**
    *   A `Label` or `Canvas` widget will be used to display the generated layout.
    *   When the "Generate" button is clicked, the backend will create a *preview* version of the collage (a smaller, scaled-down version for performance).
    *   This `Pillow` image will be converted into a `PIL.ImageTk.PhotoImage` object, which can be displayed directly in the `Tkinter` widget.

4.  **Wiring it Together (Application Workflow):**
    *   **Initial State:** Only the "Select Folder" button is active.
    *   **Folder Selected:** The application loads and analyzes the images. The other controls are enabled. Default values are populated for the dimensions and spacing.
    *   **Generate/Shuffle Clicked:**
        1.  Read the values from the dimension and spacing `Entry` widgets.
        2.  Call the `generate_layout` function from Phase 1.
        3.  The function returns a layout definition and a `Pillow` image for the preview.
        4.  Update the preview `Label` with the new image.
        5.  Enable the "Save Image" button.
    *   **Save Clicked:**
        1.  Call a final `create_full_resolution_image` function using the stored layout definition.
        2.  Open a file dialog using `tkinter.filedialog.asksaveasfilename()` to let the user choose the save location and filename (e.g., `collage.jpg`).
        3.  Save the full-size image.
        4.  Display a simple "Saved!" confirmation message.
