import unittest
import os
import tempfile
from PIL import Image
from photogrid.image_utils import analyze_images

class TestImageAnalysis(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.create_test_image(os.path.join(self.test_dir, "h1.jpg"), 400, 300)
        self.create_test_image(os.path.join(self.test_dir, "h2.jpeg"), 800, 600)
        self.create_test_image(os.path.join(self.test_dir, "v1.jpg"), 300, 400)
        self.create_test_image(os.path.join(self.test_dir, "v2.JPG"), 600, 800)
        self.create_test_image(os.path.join(self.test_dir, "square.jpg"), 500, 500)
        
        # Create non-image and non-jpeg files to be ignored
        with open(os.path.join(self.test_dir, "ignore.txt"), "w") as f:
            f.write("text")
        self.create_test_image(os.path.join(self.test_dir, "ignore.png"), 100, 100)


    def tearDown(self):
        for root, dirs, files in os.walk(self.test_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(self.test_dir)

    def create_test_image(self, path, width, height):
        img = Image.new('RGB', (width, height), color = 'red')
        img.save(path)

    def test_analyze_images(self):
        """
        Tests that analyze_images correctly identifies and categorizes jpeg images.
        """
        horizontal, vertical = analyze_images(self.test_dir)

        self.assertEqual(len(horizontal), 2)
        self.assertEqual(len(vertical), 2)

        h_paths = {img.path for img in horizontal}
        v_paths = {img.path for img in vertical}

        self.assertIn(os.path.join(self.test_dir, 'h1.jpg'), h_paths)
        self.assertIn(os.path.join(self.test_dir, 'h2.jpeg'), h_paths)
        self.assertIn(os.path.join(self.test_dir, 'v1.jpg'), v_paths)
        self.assertIn(os.path.join(self.test_dir, 'v2.JPG'), v_paths)
        
        # Square images should be ignored for now, as should other file types
        self.assertNotIn(os.path.join(self.test_dir, 'square.jpg'), h_paths)
        self.assertNotIn(os.path.join(self.test_dir, 'square.jpg'), v_paths)
        self.assertNotIn(os.path.join(self.test_dir, 'ignore.txt'), h_paths)
        self.assertNotIn(os.path.join(self.test_dir, 'ignore.png'), v_paths)

if __name__ == '__main__':
    unittest.main()
