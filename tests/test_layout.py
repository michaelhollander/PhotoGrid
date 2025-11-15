import unittest
from photogrid.image_utils import ImageInfo
from photogrid.layout import calculate_target_sizes, build_rows, justify_row

class TestLayout(unittest.TestCase):

    def test_calculate_target_sizes(self):
        """
        Tests that the calculated sizes for horizontal and vertical images
        maintain aspect ratio and have equal area.
        """
        horizontal_images = [
            ImageInfo(path='h1.jpg', width=400, height=300, aspect_ratio=4/3)
        ]
        vertical_images = [
            ImageInfo(path='v1.jpg', width=300, height=400, aspect_ratio=3/4)
        ]
        sizer = calculate_target_sizes(horizontal_images, vertical_images)
        scale = 100
        w_h, h_h, w_v, h_v = sizer(scale)

        self.assertAlmostEqual(w_h / h_h, 4/3, places=5)
        self.assertAlmostEqual(w_v / h_v, 3/4, places=5)
        self.assertAlmostEqual(w_h * h_h, w_v * h_v, places=5)
        self.assertAlmostEqual(w_h * h_h, scale**2, places=5)

    def test_build_rows(self):
        """
        Tests that images are correctly grouped into rows based on output width.
        """
        output_width = 350
        min_spacing = 10
        images = [
            {'id': 1, 'width': 100}, {'id': 2, 'width': 100}, {'id': 3, 'width': 120},
            {'id': 4, 'width': 350},
            {'id': 5, 'width': 150}, {'id': 6, 'width': 150},
        ]
        
        rows = build_rows(images, output_width, min_spacing)
        
        # We expect 3 rows:
        # 1. [1, 2, 3] (100 + 10 + 100 + 10 + 120 = 340)
        # 2. [4] (350)
        # 3. [5, 6] (150 + 10 + 150 = 310)
        self.assertEqual(len(rows), 3)
        self.assertEqual([img['id'] for img in rows[0]], [1, 2, 3])
        self.assertEqual([img['id'] for img in rows[1]], [4])
        self.assertEqual([img['id'] for img in rows[2]], [5, 6])

    def test_justify_row(self):
        """
        Tests the horizontal justification of a single row of images.
        """
        # Case 1: Normal justification
        row = [{'width': 100}, {'width': 100}, {'width': 100}]
        # Total width = 300. Leftover space = 400 - 300 = 100.
        # 2 gaps. 100 / 2 = 50 extra space per gap.
        # Min spacing = 10. Final spacing = 10 + 40 = 50.
        positions = justify_row(row, 400, 10, 100)
        self.assertAlmostEqual(positions[0]['x'], 0)
        self.assertAlmostEqual(positions[1]['x'], 100 + 50) # 150
        self.assertAlmostEqual(positions[2]['x'], 150 + 100 + 50) # 300

        # Case 2: Justification capped by max_spacing
        # Leftover space = 80. Extra space per gap = 40.
        # Min spacing = 10. Max spacing = 30.
        # Final spacing should be capped at 30.
        positions = justify_row(row, 400, 10, 30)
        self.assertAlmostEqual(positions[0]['x'], 0)
        self.assertAlmostEqual(positions[1]['x'], 100 + 30) # 130
        self.assertAlmostEqual(positions[2]['x'], 130 + 100 + 30) # 260

        # Case 3: Single image row (should be left-aligned)
        row = [{'width': 100}]
        positions = justify_row(row, 400, 10, 100)
        self.assertEqual(len(positions), 1)
        self.assertAlmostEqual(positions[0]['x'], 0)

if __name__ == '__main__':
    unittest.main()