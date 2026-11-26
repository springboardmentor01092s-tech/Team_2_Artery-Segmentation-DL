"""End-to-End Integration and System Verification Suite for CoroVision-AI."""

import os, sys, unittest, json, yaml, numpy as np, pandas as pd, torch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.preprocess import get_dataloaders
from models.unet import BaselineUNet
from models.attention_resunet import AttentionResUNet
from models.stenosis_model import StenosisClassifier, calculate_percentage_narrowing, classify_stenosis_severity
from src.vessel_analysis import postprocess_mask, extract_vessel_centerline, estimate_vessel_diameters
from src.gradcam import GradCAM, apply_colormap_on_image
from src.model_comparison import compare_models
from src.report_generator import generate_automated_reports


class TestEndToEndPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config_path = "config.yaml"
        with open(cls.config_path) as f:
            cls.cfg = yaml.safe_load(f)
        cls.dev_str = cls.cfg["training"].get("device", "cuda")
        cls.device = torch.device(cls.dev_str if (torch.cuda.is_available() and cls.dev_str == "cuda") else "cpu")

    def test_01_dataloaders_and_splits(self):
        train_ld, val_ld, test_ld, splits = get_dataloaders(self.config_path)
        self.assertEqual(len(splits["train"]), 93)
        self.assertEqual(len(splits["val"]), 20)
        self.assertEqual(len(splits["test"]), 21)

        imgs, gts, _ = next(iter(test_ld))
        self.assertEqual(imgs.shape, (imgs.shape[0], 1, 320, 320))
        self.assertTrue(0.0 <= imgs.min() and imgs.max() <= 1.0)
        self.assertTrue(0.0 <= gts.min() and gts.max() <= 1.0)

    def test_02_model_architectures_and_checkpoints(self):
        u_model = BaselineUNet(1, 1).to(self.device).eval()
        a_model = AttentionResUNet(1, 1).to(self.device).eval()
        dummy = torch.randn(2, 1, 320, 320).to(self.device)

        with torch.no_grad():
            self.assertEqual(u_model(dummy).shape, (2, 1, 320, 320))
            self.assertEqual(a_model(dummy).shape, (2, 1, 320, 320))

        for ckpt in ["best_Baseline_UNet.pth", "best_Attention_ResUNet.pth", "best_stenosis_classifier.pth"]:
            p = os.path.join(self.cfg["paths"]["checkpoints_dir"], ckpt)
            self.assertTrue(os.path.exists(p), f"Missing checkpoint: {p}")
            self.assertGreater(os.path.getsize(p), 50000)

    def test_03_morphometry_and_skeletonization(self):
        test_mask = np.zeros((320, 320), dtype=np.uint8)
        test_mask[150:170, 40:280] = 255
        test_mask[100:105, 50:55] = 255

        clean_m = postprocess_mask(test_mask, min_component_size=30, kernel_size=3)
        self.assertEqual(clean_m[102, 52], 0)
        self.assertEqual(clean_m[160, 160], 255)

        skel = extract_vessel_centerline(clean_m)
        self.assertTrue(np.sum(skel) > 0)

        morpho = estimate_vessel_diameters(clean_m, skel)
        self.assertIn("mean_diameter_px", morpho)
        self.assertAlmostEqual(morpho["mean_diameter_px"], 20.0, delta=2.5)

    def test_04_qca_narrowing_and_severity_classification(self):
        cases = [
            (10.0, 8.0, 20.0, "Normal"),
            (10.0, 6.0, 40.0, "Mild"),
            (10.0, 4.0, 60.0, "Moderate"),
            (10.0, 2.0, 80.0, "Severe"),
            (10.0, 0.0, 100.0, "Total Occlusion"),
        ]
        for rvd, mld, exp_pct, exp_sev in cases:
            pct = calculate_percentage_narrowing(rvd, mld)
            self.assertAlmostEqual(pct, exp_pct, places=2)
            self.assertEqual(classify_stenosis_severity(pct, mld, rvd)["severity_class"], exp_sev)

    def test_05_gradcam_feature_attribution(self):
        model = StenosisClassifier(2, 2).to(self.device).eval()
        gradcam = GradCAM(model)
        cam, conf, _, _ = gradcam.generate_cam(torch.randn(1, 2, 48, 48).to(self.device), target_class=1)
        gradcam.remove_hooks()

        self.assertEqual(cam.shape, (48, 48))
        self.assertTrue(0.0 <= cam.min() and cam.max() <= 1.0)
        self.assertTrue(0.0 <= conf <= 1.0)
        self.assertEqual(apply_colormap_on_image(np.full((48, 48), 128, dtype=np.uint8), cam).shape, (48, 48, 3))

    def test_06_model_comparison_engine(self):
        summary = compare_models(self.config_path)
        for k in ["metrics_comparison", "morphometry_comparison", "efficiency"]:
            self.assertIn(k, summary)

        rpt_dir = self.cfg["paths"]["reports_dir"]
        for ext in ["png", "csv", "json", "report.md"]:
            fname = f"model_comparison.{ext}" if ext != "report.md" else "model_comparison_report.md"
            self.assertTrue(os.path.exists(os.path.join(rpt_dir, fname)))

    def test_07_automated_reporting_engine(self):
        res = generate_automated_reports(self.config_path, export_formats=("pdf", "csv", "json"), patient_case_id="104")
        for k in ["pdf", "csv", "json", "patient_pdf"]:
            self.assertIn(k, res)
            self.assertTrue(os.path.exists(res[k]))
            self.assertGreater(os.path.getsize(res[k]), 500)

        df_u = pd.read_csv(res["csv"])
        self.assertEqual(len(df_u), 21)
        self.assertIn("primary_severity", df_u.columns)
        self.assertIn("max_narrowing_pct", df_u.columns)

    def test_08_stenosis_detection_and_gradcam_pipeline(self):
        summary = compare_models(self.config_path)
        self.assertIn("metrics_comparison", summary)
        self.assertIn("dice", summary["metrics_comparison"])
        self.assertIn("iou", summary["metrics_comparison"])

    def test_09_comprehensive_report_metrics_completeness(self):
        metrics_path = os.path.join(self.cfg["paths"]["reports_dir"], "comprehensive_report.json")
        self.assertTrue(os.path.exists(metrics_path))
        data = json.load(open(metrics_path))
        for k in ["report_metadata", "model_comparison", "stenosis_summary", "case_level_records"]:
            self.assertIn(k, data)
        self.assertEqual(len(data["case_level_records"]), 21)


if __name__ == "__main__":
    unittest.main()
