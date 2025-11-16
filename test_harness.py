import os
import random
from PIL import Image

# This script needs access to the photogrid modules
from photogrid.image_utils import analyze_images
from photogrid.layout import calculate_target_sizes, build_rows, justify_row

def run_test():
    """
    Runs a programmatic test of the core layout generation logic.
    """
    # --- Parameters (from the UI) ---
    folder_path = "test-images"
    output_w = 1920
    output_h = 1080
    min_space = 10
    max_space = 50
    output_filename = "test_harness_output.jpg"
    enable_cropping = True

    print(f"--- Running Test Harness ---")
    print(f"Cropping Enabled: {enable_cropping}")
    print(f"Input folder: {folder_path}")
    print(f"Output size: {output_w}x{output_h}")

    # --- Logic copied from main.py's generate_layout() ---
    h, v = analyze_images(folder_path)
    all_images = h + v
    num_images = len(all_images)
    if num_images == 0:
        print("No images found.")
        return

    random.shuffle(all_images)

    best_layout = None
    max_score = -float('inf')

    # New, smarter target scale calculation
    canvas_aspect_ratio = output_w / output_h
    avg_aspect_ratio = sum(img.aspect_ratio for img in all_images) / num_images if num_images > 0 else 1
    
    est_cols = (num_images * canvas_aspect_ratio / avg_aspect_ratio) ** 0.5
    est_cols = max(1, round(est_cols))
    
    target_w = (output_w - (est_cols - 1) * min_space) / est_cols
    target_h = target_w / avg_aspect_ratio
    target_area = target_w * target_h
    target_scale = max(1, target_area ** 0.5)
    
    print("\nSearching for optimal layout...")
    for i in range(50):
        scale = target_scale * (0.5 + (i / 49.0) * 2.5)
        if scale == 0: continue

        if enable_cropping:
            target_aspect_ratio = output_w / output_h
            img_h = scale
            img_w = scale * target_aspect_ratio
            sized_images = [{'path': img.path, 'width': img_w, 'height': img_h} for img in all_images]
        else:
            h_imgs = [img for img in all_images if img.aspect_ratio > 1]
            v_imgs = [img for img in all_images if img.aspect_ratio < 1]
            sizer = calculate_target_sizes(h_imgs, v_imgs)
            w_h, h_h, w_v, h_v = sizer(scale)
            sized_images = []
            for img_info in all_images:
                if img_info.aspect_ratio > 1: # Horizontal
                    sized_images.append({'path': img_info.path, 'width': w_h, 'height': h_h})
                else: # Vertical
                    sized_images.append({'path': img_info.path, 'width': w_v, 'height': h_v})

        rows_of_images = build_rows(sized_images, output_w, min_space)

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
            best_layout = final_layout

    final_photo_area = sum(img['width'] * img['height'] for img in best_layout) if best_layout else 0
    final_coverage = final_photo_area / (output_w * output_h)
    print(f"Best layout found with {final_coverage * 100:.1f}% area coverage.")

    # --- Logic copied from main.py's save_image() ---
    if not best_layout:
        print("Could not generate a valid layout.")
        return

    print(f"Saving final image to {output_filename}...")
    final_image = Image.new('RGB', (output_w, output_h), 'white')
    target_aspect_ratio = output_w / output_h

    for img_layout in best_layout:
        with Image.open(img_layout['path']) as img:
            if enable_cropping:
                img = crop_to_aspect_ratio(img, target_aspect_ratio)
            img = img.resize((int(img_layout['width']), int(img_layout['height'])), Image.Resampling.LANCZOS)
            final_image.paste(img, (int(img_layout['x']), int(img_layout['y'])))
    
    final_image.save(output_filename)
    print("--- Test Complete ---")

if __name__ == "__main__":
    from photogrid.image_utils import crop_to_aspect_ratio
    run_test()
