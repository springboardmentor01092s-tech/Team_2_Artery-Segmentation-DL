import unittest
from app.evaluation_counts import binary_count_summary, lesion_count_summary


class SavedCountTests(unittest.TestCase):
    def test_pixel_metrics_keep_unit_and_micro_definition(self):
        result = binary_count_summary(dict(tp=2,fp=1,fn=1,tn=6), unit='pixel')
        self.assertEqual(result['accuracy'], .8)
        self.assertAlmostEqual(result['dice'], 2/3)
        self.assertEqual(result['iou'], .5)
        self.assertAlmostEqual(result['specificity'], 6/7)
        self.assertAlmostEqual(result['false_positive_rate'], 1/7)
        self.assertEqual(result['recall'], result['sensitivity'])
        self.assertEqual(result['aggregation'], 'micro_from_supplied_counts')

    def test_detection_has_no_invented_true_negatives(self):
        result = lesion_count_summary(dict(tp=2,fp=1,fn=1), images=4)
        self.assertEqual(result['false_positives_per_image'], .25)
        self.assertAlmostEqual(result['f1'], 2/3)
        self.assertAlmostEqual(result['false_negative_rate'], 1/3)
        for key in ('tn','accuracy','specificity','false_positive_rate'):
            self.assertIsNone(result[key])
        with self.assertRaises(ValueError):
            binary_count_summary(dict(tp=2,fp=1,fn=1,tn=6), unit='lesion')

    def test_undefined_rates_do_not_become_perfect_results(self):
        result = binary_count_summary(dict(tp=0,fp=0,fn=0,tn=0), unit='pixel')
        for key in ('accuracy','precision','recall','dice','iou','specificity'):
            self.assertIsNone(result[key])
        empty = lesion_count_summary(dict(tp=0,fp=0,fn=0), images=2)
        self.assertIsNone(empty['f1'])
        self.assertEqual(empty['false_positives_per_image'], 0)

    def test_invalid_counts_and_support_fail(self):
        for invalid in (True,-1,1.0,float('nan')):
            with self.assertRaises(ValueError):
                lesion_count_summary(dict(tp=invalid,fp=1,fn=1), images=2)
        with self.assertRaises(ValueError):
            lesion_count_summary(dict(tp=1,fp=1,fn=1,tn=4), images=2)
        for images in (True,0,-1,1.5):
            with self.assertRaises(ValueError):
                lesion_count_summary(dict(tp=1,fp=1,fn=1), images=images)
