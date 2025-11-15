import unittest
from photogrid.image_utils import ImageInfo
from photogrid.layout import calculate_target_sizes, build_rows

class TestLayout(unittest.TestCase):

    def test_calculate_target_sizes(self):
        """
        Tests that the calculated sizes for horizontal and vertical images
        maintain aspect ratio and have equal area.
        """
        # Mock image data with different aspect ratios
        horizontal_images = [
            ImageInfo(path='h1.jpg', width=400, height=300, aspect_ratio=4/3),
            ImageInfo(path='h2.jpg', width=1600, height=900, aspect_ratio=16/9)
        ] # Average AR_h = (4/3 + 16/9) / 2 = (12/9 + 16/9) / 2 = (28/9) / 2 = 14/9

        vertical_images = [
            ImageInfo(path='v1.jpg', width=300, height=400, aspect_ratio=3/4),
            ImageInfo(path='v2.jpg', width=900, height=1600, aspect_ratio=9/16)
        ] # Average AR_v = (3/4 + 9/16) / 2 = (12/16 + 9/16) / 2 = (21/16) / 2 = 21/32

        # The function should return a "sizer" function that takes a scaling factor
        sizer = calculate_target_sizes(horizontal_images, vertical_images)

        # Let's use a scaling factor of 100 for simplicity
        scale = 100
        w_h, h_h, w_v, h_v = sizer(scale)

        # 1. Check if aspect ratios are preserved
        avg_ar_h = 14/9
        avg_ar_v = 21/32
        self.assertAlmostEqual(w_h / h_h, avg_ar_h, places=5)
        self.assertAlmostEqual(w_v / h_v, avg_ar_v, places=5)

        # 2. Check if areas are equal
        area_h = w_h * h_h
        area_v = w_v * h_v
        self.assertAlmostEqual(area_h, area_v, places=5)

        # 3. Check that the scale factor is working
        # Area = scale^2, so let's test this relationship
        self.assertAlmostEqual(area_h, scale**2, places=5)

    def test_build_rows(self):
        """
        Tests that images are correctly grouped into rows based on output width.
        """
        # Mock images with simple integer widths
        images = [
            {'id': 1, 'width': 100}, {'id': 2, 'width': 100}, {'id': 3, 'width': 100},
            {'id': 4, 'width': 250}, {'id': 5, 'width': 100}, {'id': 6, 'width': 250},
        ]
        output_width = 350
        min_spacing = 10

        rows = build_rows(images, output_width, min_spacing)

        self.assertEqual(len(rows), 3)
        # Row 1: 100 + 10 + 100 + 10 + 100 = 320 <= 350. Fits.
        self.assertEqual([img['id'] for img in rows[0]], [1, 2, 3])
        # Row 2: 250. Next image (100) doesn't fit (250 + 10 + 100 > 350).
        self.assertEqual([img['id'] for img in rows[1]], [4])
        # Row 3: 100 + 10 + 250 = 360. Wait. The logic should be:
        # Current row width + spacing + next image width <= output_width
        # Row 2 try 1: img 4 (250). Current width = 250.
        # Row 2 try 2: img 5 (100). 250 + 10 + 100 = 360 > 350. No fit.
        # So row 2 is just [4].
        # Row 3 try 1: img 5 (100). Current width = 100.
        # Row 3 try 2: img 6 (250). 100 + 10 + 250 = 360 > 350. No fit.
        # So row 3 is just [5].
        # Row 4 would be [6].
        # Let's adjust the test to reflect this simpler logic.
        
        images = [
            {'id': 1, 'width': 100}, {'id': 2, 'width': 100}, {'id': 3, 'width': 120},
            {'id': 4, 'width': 350},
            {'id': 5, 'width': 150}, {'id': 6, 'width': 150},
        ]
        
        rows = build_rows(images, output_width, min_spacing)
        
        print("Generated rows:", [[img['id'] for img in row] for row in rows])

        self.assertEqual(len(rows), 3)
        # Row 1: 100 + 10 + 100 + 10 + 120 = 340 <= 350. Fits.
        self.assertEqual([img['id'] for img in rows[0]], [1, 2, 3])
        # Row 2: 350. Fits exactly.
        self.assertEqual([img['id'] for img in rows[1]], [4])
        # Row 3: 150 + 10 + 150 = 310 <= 350. Fits.
        self.assertEqual([img['id'] for img in rows[2]], [5, 6])

if __name__ == '__main__':
    unittest.main()
