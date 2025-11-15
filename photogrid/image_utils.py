import os
from PIL import Image
from collections import namedtuple

ImageInfo = namedtuple('ImageInfo', ['path', 'width', 'height', 'aspect_ratio'])

def analyze_images(folder_path):
    """
    Scans a directory for JPEG images and categorizes them into horizontal and vertical lists.

    Args:
        folder_path (str): The path to the directory to scan.

    Returns:
        tuple: A tuple containing two lists: (horizontal_images, vertical_images)
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
                width, height = img.size
                
                if width == height:
                    continue # Ignore square images as per the test

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
