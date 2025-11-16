import os
from PIL import Image, ImageOps
from collections import namedtuple

ImageInfo = namedtuple('ImageInfo', ['path', 'width', 'height', 'aspect_ratio'])

def analyze_images(folder_path):
    """
    Scans a directory for JPEG images and categorizes them into horizontal and vertical lists.
    """
    horizontal_images = []
    vertical_images = []
    
    valid_extensions = {'.jpg', '.jpeg'}

    for filename in os.listdir(folder_path):
        try:
            name, ext = os.path.splitext(filename)
            if ext.lower() not in valid_extensions:
                continue

            path = os.path.join(folder_path, filename)
            with Image.open(path) as img:
                # Apply EXIF orientation before getting dimensions
                img = ImageOps.exif_transpose(img)
                width, height = img.size
                
                if width == height:
                    continue # Ignore square images

                aspect_ratio = width / height
                info = ImageInfo(path=path, width=width, height=height, aspect_ratio=aspect_ratio)

                if aspect_ratio > 1:
                    horizontal_images.append(info)
                else:
                    vertical_images.append(info)
        except Exception as e:
            # Ignore files that are not valid images
            print(f"Could not process file {filename}: {e}")
            continue
            
    return horizontal_images, vertical_images

def crop_to_aspect_ratio(image, target_aspect_ratio):
    """
    Crops an image to match a target aspect ratio, cutting from the center.

    Args:
        image (PIL.Image): The image to crop.
        target_aspect_ratio (float): The desired aspect ratio (width / height).

    Returns:
        PIL.Image: The cropped image.
    """
    img_width, img_height = image.size
    img_aspect_ratio = img_width / img_height

    if img_aspect_ratio > target_aspect_ratio:
        # Image is wider than target, crop the sides
        new_width = int(target_aspect_ratio * img_height)
        offset = (img_width - new_width) / 2
        box = (offset, 0, img_width - offset, img_height)
    else:
        # Image is taller than target, crop the top and bottom
        new_height = int(img_width / target_aspect_ratio)
        offset = (img_height - new_height) / 2
        box = (0, offset, img_width, img_height - offset)
        
    return image.crop(box)
