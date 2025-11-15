import math

def calculate_target_sizes(horizontal_images, vertical_images):
    """
    Calculates the average aspect ratios and returns a function that can generate
    target dimensions for a given scaling factor.

    The returned function solves the system of equations:
    1. w_h / h_h = ar_h
    2. w_v / h_v = ar_v
    3. w_h * h_h = w_v * h_v = area
    
    If we set area = scale^2, we can solve for the dimensions:
    w_h = scale * sqrt(ar_h)
    h_h = scale / sqrt(ar_h)
    w_v = scale * sqrt(ar_v)
    h_v = scale / sqrt(ar_v)

    Args:
        horizontal_images (list): A list of ImageInfo objects for horizontal images.
        vertical_images (list): A list of ImageInfo objects for vertical images.

    Returns:
        function: A function that takes a single argument `scale` and returns a
                  tuple of (w_h, h_h, w_v, h_v).
    """
    
    if not horizontal_images or not vertical_images:
        # Handle cases with no images of one type, though the layout will be trivial
        avg_ar_h = 16/9
        avg_ar_v = 9/16
    else:
        avg_ar_h = sum(img.aspect_ratio for img in horizontal_images) / len(horizontal_images)
        avg_ar_v = sum(img.aspect_ratio for img in vertical_images) / len(vertical_images)

    sqrt_ar_h = math.sqrt(avg_ar_h)
    sqrt_ar_v = math.sqrt(avg_ar_v)

    def sizer(scale):
        w_h = scale * sqrt_ar_h
        h_h = scale / sqrt_ar_h
        w_v = scale * sqrt_ar_v
        h_v = scale / sqrt_ar_v
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

    rows = []
    current_row = []

    for image in images:
        if not current_row:
            current_row.append(image)
        else:
            current_row_width = sum(img['width'] for img in current_row)
            potential_width = current_row_width + (len(current_row) * min_spacing) + image['width']
            
            if potential_width <= output_width:
                current_row.append(image)
            else:
                rows.append(current_row)
                current_row = [image]
    
    if current_row:
        rows.append(current_row)
        
    return rows
