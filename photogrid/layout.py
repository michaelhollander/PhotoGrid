import math

def calculate_target_sizes(horizontal_images, vertical_images):
    """
    Calculates the average aspect ratios and returns a function that can generate
    target dimensions for a given scaling factor.

    The returned function now assumes:
    1. All horizontal images will have a height equal to 'scale'.
    2. All vertical images will have a width equal to 'scale'.
    3. Aspect ratios are preserved.

    Args:
        horizontal_images (list): A list of ImageInfo objects for horizontal images.
        vertical_images (list): A list of ImageInfo objects for vertical images.

    Returns:
        function: A function that takes a single argument `scale` and returns a
                  tuple of (w_h, h_h, w_v, h_v).
    """
    
    avg_ar_h = sum(img.aspect_ratio for img in horizontal_images) / len(horizontal_images) if horizontal_images else 1.0
    avg_ar_v = sum(img.aspect_ratio for img in vertical_images) / len(vertical_images) if vertical_images else 1.0

    def sizer(scale):
        # For horizontal images, scale is the height
        h_h = scale
        w_h = scale * avg_ar_h
        
        # For vertical images, scale is the width
        w_v = scale
        h_v = scale / avg_ar_v
        
        return w_h, h_h, w_v, h_v

    return sizer
def build_rows(images, output_width, min_spacing):
    """
    Groups a list of images into rows based on a greedy algorithm.

    Args:
        images (list): A list of image-like objects that have a 'width' attribute.
        output_width (float): The maximum width of a row.
        min_spacing (float): The minimum spacing between images in a row.

    Returns:
        list: A list of lists, where each inner list represents a row of images.
    """
    if not images:
        return []

    # Start with the first image in the first row
    rows = [[images[0]]]
    
    # Iterate over the rest of the images
    for image in images[1:]:
        current_row = rows[-1]
        
        # Calculate the width of the current row if we add the new image
        current_row_width = sum(img['width'] for img in current_row)
        # The number of spaces in the potential new row is len(current_row)
        potential_width = current_row_width + (len(current_row) * min_spacing) + image['width']

        if potential_width <= output_width:
            # Add the image to the current row
            current_row.append(image)
        else:
            # Start a new row
            rows.append([image])
            
    return rows

def justify_row(row, output_width, min_spacing, max_spacing):
    """
    Calculates the x-positions for images in a single row to justify them.
    """
    if not row:
        return []

    if len(row) <= 1:
        return [{'image': row[0], 'x': 0}]

    total_image_width = sum(img['width'] for img in row)
    num_gaps = len(row) - 1
    
    leftover_space = output_width - total_image_width - (num_gaps * min_spacing)
    
    extra_spacing_per_gap = 0
    if leftover_space > 0:
        extra_spacing_per_gap = leftover_space / num_gaps
    
    final_spacing = min_spacing + extra_spacing_per_gap
    final_spacing = min(final_spacing, max_spacing)

    positions = []
    current_x = 0
    for i, image in enumerate(row):
        positions.append({'image': image, 'x': current_x})
        current_x += image['width'] + final_spacing
        
    return positions
