"""API Verification Suite for CoroVision-AI (Programmatic & REST)."""

import os, sys, time, json, unittest, requests, cv2, numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.api import CoroVisionAPI, CoroVisionRequestHandler, run_api_server


class TestCoroVisionAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config_path = "config.yaml"
        cls.api = CoroVisionAPI(cls.config_path)
        CoroVisionRequestHandler.api = cls.api

        cls.port = 8765
        cls.base_url = f"http://127.0.0.1:{cls.port}"
        try:
            cls.server, cls.server_thread = run_api_server(host="127.0.0.1", port=cls.port, config_path=cls.config_path, blocking=False)
            time.sleep(0.5)
        except Exception:
            cls.server = None

    @classmethod
    def tearDownClass(cls):
        if cls.server:
            try:
                cls.server.shutdown()
                cls.server.server_close()
            except Exception:
                pass

    def _request(self, method: str, path: str, payload: dict = None) -> tuple:
        try:
            if method == "GET":
                resp = requests.get(f"{self.base_url}{path}", timeout=5)
            else:
                resp = requests.post(f"{self.base_url}{path}", json=payload, timeout=15)
            return resp.status_code, resp.json()
        except (requests.exceptions.ConnectionError, PermissionError, OSError):
            return CoroVisionRequestHandler.handle_request_dict(method, path, payload)

    # --- Programmatic API Tests ---

    def test_01_programmatic_status(self):
        status = self.api.get_status()
        self.assertEqual(status["status"], "operational")
        self.assertEqual(status["service"], "CoroVision-AI")
        self.assertIn("attention_resunet", status["available_models"])
        self.assertEqual(status["dataset_splits"]["test_cases"], 21)

    def test_02_programmatic_segmentation(self):
        dummy_img = np.random.randint(20, 200, (320, 320), dtype=np.uint8)
        res = self.api.segment_image(dummy_img, model_name="attention_resunet")
        self.assertIn("clean_mask", res)
        self.assertEqual(res["clean_mask"].shape, (320, 320))
        self.assertIn("vessel_area_pct", res)

    def test_03_programmatic_morphometry(self):
        mask = np.zeros((320, 320), dtype=np.uint8)
        mask[100:115, 50:250] = 255
        morpho = self.api.extract_morphometry(mask)
        self.assertIn("centerline_length_px", morpho)
        self.assertIn("mean_diameter_px", morpho)
        self.assertGreater(morpho["centerline_length_px"], 100)

    def test_04_programmatic_case_processing(self):
        res = self.api.process_case("104")
        self.assertEqual(res["case_id"], "104")
        self.assertIn("primary_severity", res)
        self.assertIn("max_narrowing_pct", res)
        self.assertGreater(res["total_lesions_count"], 0)

    # --- REST HTTP API Tests ---

    def test_05_http_get_health(self):
        code, data = self._request("GET", "/api/health")
        self.assertEqual(code, 200)
        self.assertEqual(data["status"], "healthy")

    def test_06_http_get_status(self):
        code, data = self._request("GET", "/api/status")
        self.assertEqual(code, 200)
        self.assertEqual(data["status"], "operational")
        self.assertIn("device", data)

    def test_07_http_get_compare(self):
        code, data = self._request("GET", "/api/compare")
        self.assertEqual(code, 200)
        self.assertIn("metrics_comparison", data)
        self.assertIn("efficiency", data)

    def test_08_http_get_report_summary(self):
        code, data = self._request("GET", "/api/reports/summary")
        self.assertEqual(code, 200)
        self.assertIn("report_metadata", data)
        self.assertIn("case_level_records", data)

    def test_09_http_post_segment(self):
        code, data = self._request("POST", "/api/segment", {"case_id": "104", "model": "attention_resunet"})
        self.assertEqual(code, 200)
        self.assertEqual(data["case_id"], "104")
        self.assertIn("vessel_area_pct", data)

    def test_10_http_post_process_case(self):
        code, data = self._request("POST", "/api/process_case", {"case_id": "104"})
        self.assertEqual(code, 200)
        self.assertEqual(data["case_id"], "104")
        self.assertIn("primary_severity", data)
        self.assertIn("lesions_summary", data)

    def test_11_http_post_report(self):
        code, data = self._request("POST", "/api/report", {"formats": ["json", "csv"], "patient_case_id": "104"})
        self.assertEqual(code, 200)
        self.assertEqual(data["status"], "success")
        self.assertIn("generated_files", data)

    def test_12_http_error_handling(self):
        code_404, _ = self._request("GET", "/api/unknown_endpoint")
        self.assertEqual(code_404, 404)
        code_400, _ = self._request("POST", "/api/process_case", {})
        self.assertEqual(code_400, 400)

    # --- Security Testing ---

    def test_13_security_path_traversal(self):
        for bad_id in ["../../etc/passwd", "..\\..\\boot.ini", "/root/secret", "case*;", "../104"]:
            self.assertEqual(self._request("POST", "/api/segment", {"case_id": bad_id})[0], 400)
            self.assertEqual(self._request("POST", "/api/process_case", {"case_id": bad_id})[0], 400)

    def test_14_security_report_injection(self):
        self.assertEqual(self._request("POST", "/api/report", {"formats": ["exe", "../../hack"]})[0], 400)
        self.assertEqual(self._request("POST", "/api/report", {"patient_case_id": "../../malicious"})[0], 400)

    def test_15_security_payload_limit(self):
        handler = CoroVisionRequestHandler.__new__(CoroVisionRequestHandler)
        handler.headers = {"Content-Length": str(20 * 1024 * 1024)}
        with self.assertRaises(OverflowError):
            handler._read_json_body()

    # --- Performance Testing ---

    def test_16_performance_endpoints_latency(self):
        self._request("GET", "/api/health")

        t0 = time.perf_counter()
        code, _ = self._request("GET", "/api/health")
        self.assertEqual(code, 200)
        self.assertLess((time.perf_counter() - t0) * 1000.0, 50.0)

        t0 = time.perf_counter()
        code, _ = self._request("GET", "/api/status")
        self.assertEqual(code, 200)
        self.assertLess((time.perf_counter() - t0) * 1000.0, 60.0)

        t0 = time.perf_counter()
        code, _ = self._request("POST", "/api/process_case", {"case_id": "104"})
        self.assertEqual(code, 200)
        self.assertLess((time.perf_counter() - t0) * 1000.0, 750.0)

    def test_17_performance_concurrent_load(self):
        latencies = []
        for _ in range(15):
            t0 = time.perf_counter()
            code, _ = self._request("POST", "/api/segment", {"case_id": "104"})
            self.assertEqual(code, 200)
            latencies.append((time.perf_counter() - t0) * 1000.0)

        self.assertEqual(len(latencies), 15)
        self.assertLess(float(np.mean(latencies)), 100.0)
        self.assertLess(float(np.percentile(latencies, 95)), 150.0)

    def test_18_security_injection_payloads(self):
        payloads = [
            "' OR '1'='1", "1; DROP TABLE users; --", "admin'--", "1 | whoami",
            "1; ls -la", "1 && net user", "`ping 127.0.0.1`", "${IFS}cat${IFS}/etc/passwd"
        ]
        for inj in payloads:
            self.assertEqual(self._request("POST", "/api/segment", {"case_id": inj})[0], 400)
            self.assertEqual(self._request("POST", "/api/process_case", {"case_id": inj})[0], 400)

    def test_19_security_auth_and_information_disclosure(self):
        CoroVisionRequestHandler.auth_token = "secret_clinical_token_123"
        try:
            self.assertEqual(CoroVisionRequestHandler.handle_request_dict("GET", "/api/status", headers={})[0], 401)
            self.assertEqual(CoroVisionRequestHandler.handle_request_dict("GET", "/api/status", headers={"Authorization": "Bearer wrong"})[0], 401)
            self.assertEqual(CoroVisionRequestHandler.handle_request_dict("GET", "/api/status", headers={"Authorization": "Bearer secret_clinical_token_123"})[0], 200)
        finally:
            CoroVisionRequestHandler.auth_token = None

        code_err, err_data = CoroVisionRequestHandler.handle_request_dict("POST", "/api/segment", {"case_id": "99999"})
        self.assertEqual(code_err, 404)
        err_msg = err_data.get("error", "")
        self.assertNotIn("D:\\", err_msg)
        self.assertNotIn("C:\\", err_msg)

    def test_20_performance_resource_usage(self):
        import psutil
        process = psutil.Process()
        ram_before_mb = process.memory_info().rss / (1024 * 1024)
        for _ in range(5):
            self.api.process_case("104")
        ram_delta = (process.memory_info().rss / (1024 * 1024)) - ram_before_mb
        self.assertLess(ram_delta, 75.0)

    def test_21_performance_bottleneck_profiling(self):
        img = cv2.imread(os.path.join(self.api.cfg["dataset"]["images_dir"], "104.png"), cv2.IMREAD_GRAYSCALE)

        t0 = time.perf_counter()
        seg_res = self.api.segment_image(img, "attention_resunet")
        t_seg = (time.perf_counter() - t0) * 1000.0

        t0 = time.perf_counter()
        morpho = self.api.extract_morphometry(seg_res["clean_mask"])
        t_morph = (time.perf_counter() - t0) * 1000.0

        t0 = time.perf_counter()
        lesions = self.api.detect_stenosis(img, seg_res["clean_mask"])
        t_sten = (time.perf_counter() - t0) * 1000.0

        self.assertLess(t_seg, 150.0)
        self.assertLess(t_morph, 100.0)
        self.assertLess(t_sten, 600.0)

    def test_22_api_json_and_error_contract(self):
        code, err = self._request("POST", "/api/segment", {"image_base64": "invalid_base64_data"})
        self.assertEqual(code, 400)
        self.assertIn("error", err)

    def test_23_programmatic_report_export_validation(self):
        res = self.api.generate_reports(export_formats=["pdf", "csv", "json"], patient_case_id="104")
        for k in ["pdf", "csv", "json"]:
            self.assertIn(k, res)
            self.assertTrue(os.path.exists(res[k]))

    def test_24_model_comparison_statistics_structure(self):
        res = self.api.compare_models()
        self.assertIn("metrics_comparison", res)
        for metric in ["dice", "iou", "precision", "recall", "specificity"]:
            self.assertIn(metric, res["metrics_comparison"])
            self.assertIn("p_value", res["metrics_comparison"][metric])

    def test_25_security_cross_site_and_sanitization(self):
        for xss in ["<script>alert('XSS')</script>", "<img src=x onerror=alert(1)>", "104<script>"]:
            self.assertEqual(self._request("POST", "/api/process_case", {"case_id": xss})[0], 400)

    def test_26_performance_optimization_benchmark(self):
        t0 = time.perf_counter()
        res = self.api.process_case("104")
        self.assertLess((time.perf_counter() - t0) * 1000.0, 750.0)
        self.assertIn("primary_severity", res)
        self.assertGreater(res["total_lesions_count"], 0)


if __name__ == "__main__":
    unittest.main()
