"""Unified Programmatic and REST API for CoroVision-AI."""

import os, sys, json, yaml, cv2, numpy as np, torch, threading
from http.server import HTTPServer, BaseHTTPRequestHandler

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.unet import BaselineUNet
from models.attention_resunet import AttentionResUNet
from models.stenosis_model import StenosisClassifier
from src.vessel_analysis import postprocess_mask, extract_vessel_centerline, estimate_vessel_diameters
from src.stenosis_detection import detect_and_localize_stenosis
from src.gradcam import GradCAM
from src.model_comparison import compare_models
from src.report_generator import generate_automated_reports


def is_safe_identifier(val) -> bool:
    return bool(val and str(val).strip().replace("_", "").replace("-", "").isalnum())


def sanitize_error(e: Exception) -> str:
    import re
    msg = str(e)
    msg = re.sub(r"[A-Za-z]:\\[^ \t\n\r\f\v'\"]+", "[REDACTED_PATH]", msg)
    return re.sub(r"/(?:[^ \t\n\r\f\v'\"]+/)+[^ \t\n\r\f\v'\"]*", "[REDACTED_PATH]", msg)


class CoroVisionAPI:
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        with open(config_path, "r") as f:
            self.cfg = yaml.safe_load(f)

        dev_str = self.cfg["training"].get("device", "cuda")
        self.device = torch.device(dev_str if (torch.cuda.is_available() and dev_str == "cuda") else "cpu")
        self.models = {}
        self.gradcam = None
        self._load_checkpoints()

    def _load_checkpoints(self):
        ckpt_dir = self.cfg["paths"]["checkpoints_dir"]
        in_ch, num_cls = self.cfg["dataset"].get("in_channels", 1), self.cfg["dataset"].get("num_classes", 1)

        model_specs = [
            ("baseline_unet", BaselineUNet(in_ch, num_cls, self.cfg["models"]["baseline_unet"].get("features", [32, 64, 128, 256, 512])), "best_Baseline_UNet.pth"),
            ("attention_resunet", AttentionResUNet(in_ch, num_cls, self.cfg["models"]["attention_resunet"].get("features", [32, 64, 128, 256, 512])), "best_Attention_ResUNet.pth"),
        ]
        for name, model, ckpt_name in model_specs:
            p = os.path.join(ckpt_dir, ckpt_name)
            if os.path.exists(p):
                model.load_state_dict(torch.load(p, map_location=self.device)["model_state_dict"])
                self.models[name] = model.to(self.device).eval()

        s_p = os.path.join(ckpt_dir, "best_stenosis_classifier.pth")
        if os.path.exists(s_p):
            s_m = StenosisClassifier(2, 2)
            s_m.load_state_dict(torch.load(s_p, map_location=self.device)["model_state_dict"])
            self.models["stenosis_classifier"] = s_m.to(self.device).eval()
            self.gradcam = GradCAM(s_m)

    def get_status(self) -> dict:
        splits_f = self.cfg["dataset"]["splits_file"]
        splits = json.load(open(splits_f)) if os.path.exists(splits_f) else {"train": [], "val": [], "test": []}
        return {
            "status": "operational", "service": "CoroVision-AI", "version": "1.0.0",
            "device": str(self.device), "available_models": list(self.models.keys()),
            "dataset_splits": {
                "train_cases": len(splits.get("train", [])),
                "val_cases": len(splits.get("val", [])),
                "test_cases": len(splits.get("test", [])),
            },
        }

    def segment_image(self, image: np.ndarray, model_name: str = "attention_resunet") -> dict:
        if model_name not in self.models:
            raise ValueError(f"Model '{model_name}' not loaded. Available: {list(self.models.keys())}")

        h, w = image.shape[:2]
        img_t = torch.tensor((image.astype(np.float32) / 255.0).reshape(1, 1, h, w), dtype=torch.float32).to(self.device)
        with torch.no_grad():
            prob = torch.sigmoid(self.models[model_name](img_t)).squeeze().cpu().numpy()

        clean_mask = postprocess_mask(
            (prob >= 0.5).astype(np.uint8) * 255,
            min_component_size=self.cfg["postprocessing"].get("min_component_size", 40),
            kernel_size=self.cfg["postprocessing"].get("morphology_kernel_size", 3)
        )
        return {
            "model_used": model_name, "raw_mask": (prob >= 0.5).astype(np.uint8) * 255, "clean_mask": clean_mask,
            "vessel_pixels": int(np.sum(clean_mask > 0)),
            "vessel_area_pct": round(float(np.mean(clean_mask > 0) * 100.0), 3),
        }

    def extract_morphometry(self, clean_mask: np.ndarray) -> dict:
        skel = extract_vessel_centerline(clean_mask)
        return {k: v for k, v in estimate_vessel_diameters(clean_mask, skel).items() if k != "distance_map"}

    def detect_stenosis(self, image: np.ndarray, mask: np.ndarray) -> list:
        if "stenosis_classifier" not in self.models:
            raise RuntimeError("StenosisClassifier model checkpoint not loaded.")
        return detect_and_localize_stenosis(image, mask, self.models["stenosis_classifier"], self.device, self.cfg, gradcam=self.gradcam)

    def compare_models(self) -> dict:
        return compare_models(self.config_path)

    def generate_reports(self, export_formats=("pdf", "csv", "json"), patient_case_id: str = None) -> dict:
        return generate_automated_reports(self.config_path, export_formats, patient_case_id)

    def process_case(self, case_id: str, model_name: str = "attention_resunet") -> dict:
        if not is_safe_identifier(case_id):
            raise ValueError(f"Invalid case_id '{case_id}': alphanumeric only.")
        clean_id = os.path.basename(str(case_id).strip())
        img_path = os.path.join(self.cfg["dataset"]["images_dir"], f"{clean_id}.png")
        if not os.path.exists(img_path):
            raise FileNotFoundError(f"Case image not found: {img_path}")

        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        seg_res = self.segment_image(img, model_name=model_name)
        clean_m = seg_res["clean_mask"]
        morpho = self.extract_morphometry(clean_m)
        lesions = self.detect_stenosis(img, clean_m)
        top = lesions[0] if lesions else None

        return {
            "case_id": str(case_id), "model_used": model_name,
            "vessel_area_pct": seg_res["vessel_area_pct"],
            "centerline_length_px": morpho.get("centerline_length_px"),
            "mean_diameter_px": morpho.get("mean_diameter_px"),
            "primary_severity": top["severity"] if top else "Normal",
            "max_narrowing_pct": top["narrowing_pct"] if top else 0.0,
            "primary_mld_px": top["mld_px"] if top else 0.0,
            "primary_rvd_px": top["rvd_px"] if top else 0.0,
            "total_lesions_count": len(lesions),
            "lesions_summary": [{
                "lesion_id": f"{case_id}_L{i}", "severity": l["severity"],
                "narrowing_pct": l["narrowing_pct"], "mld_px": l["mld_px"],
                "rvd_px": l["rvd_px"], "confidence": l["confidence"],
            } for i, l in enumerate(lesions, 1)],
        }


class CoroVisionRequestHandler(BaseHTTPRequestHandler):
    api = None
    auth_token = None

    def _send_json(self, status_code: int, data: dict):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode("utf-8"))

    def _read_json_body(self) -> dict:
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            raise ValueError("Invalid Content-Length header")
        if content_length < 0 or content_length > 10 * 1024 * 1024:
            raise OverflowError("Payload exceeds 10MB maximum limit")
        return json.loads(self.rfile.read(content_length).decode("utf-8")) if content_length > 0 else {}

    @classmethod
    def handle_request_dict(cls, method: str, path: str, body: dict = None, headers: dict = None) -> tuple:
        body = body or {}
        headers = headers or {}

        if path != "/api/health" and cls.auth_token:
            auth_h = headers.get("Authorization") or headers.get("authorization", "")
            if auth_h != f"Bearer {cls.auth_token}":
                return 401, {"error": "Unauthorized: valid Bearer token required."}

        if method == "GET":
            if path == "/api/health":
                return 200, {"status": "healthy", "service": "CoroVision-AI", "version": "1.0.0"}
            if path == "/api/status":
                return 200, cls.api.get_status()
            if path == "/api/compare":
                try: return 200, cls.api.compare_models()
                except Exception as e: return 500, {"error": sanitize_error(e)}
            if path == "/api/reports/summary":
                rpt_p = os.path.join(cls.api.cfg["paths"]["reports_dir"], "comprehensive_report.json")
                return (200, json.load(open(rpt_p))) if os.path.exists(rpt_p) else (404, {"error": "Comprehensive report not found. Generate it first via POST /api/report"})
            return 404, {"error": f"Endpoint '{path}' not found."}

        if method == "POST":
            cid = body.get("case_id")
            if path == "/api/segment":
                if not is_safe_identifier(cid):
                    return 400, {"error": "Invalid or missing 'case_id'. Must be alphanumeric."}
                try:
                    clean_id = os.path.basename(str(cid).strip())
                    img = cv2.imread(os.path.join(cls.api.cfg["dataset"]["images_dir"], f"{clean_id}.png"), cv2.IMREAD_GRAYSCALE)
                    if img is None:
                        return 404, {"error": f"Image for case {clean_id} not found."}
                    res = cls.api.segment_image(img, model_name=body.get("model", "attention_resunet"))
                    clean_res = {k: v for k, v in res.items() if not isinstance(v, np.ndarray)}
                    clean_res["case_id"] = str(clean_id)
                    return 200, clean_res
                except Exception as e:
                    return 500, {"error": sanitize_error(e)}

            if path == "/api/process_case":
                if not is_safe_identifier(cid):
                    return 400, {"error": "Invalid or missing 'case_id'. Must be alphanumeric."}
                try:
                    return 200, cls.api.process_case(str(os.path.basename(str(cid).strip())))
                except Exception as e:
                    return 500, {"error": sanitize_error(e)}

            if path == "/api/report":
                formats = body.get("formats", ["pdf", "csv", "json"])
                if not isinstance(formats, (list, tuple)) or not all(f in ["pdf", "csv", "json"] for f in formats):
                    return 400, {"error": "Invalid formats. Supported: ['pdf', 'csv', 'json']"}
                pid = body.get("patient_case_id")
                if pid and not is_safe_identifier(pid):
                    return 400, {"error": "Invalid 'patient_case_id'. Must be alphanumeric."}
                try:
                    clean_pid = os.path.basename(str(pid).strip()) if pid else None
                    return 200, {"status": "success", "generated_files": cls.api.generate_reports(export_formats=formats, patient_case_id=clean_pid)}
                except Exception as e:
                    return 500, {"error": sanitize_error(e)}

            return 404, {"error": f"Endpoint '{path}' not found."}

        return 405, {"error": "Method not allowed"}

    def do_GET(self):
        status, data = self.handle_request_dict("GET", self.path, headers=dict(self.headers))
        self._send_json(status, data)

    def do_POST(self):
        try:
            body = self._read_json_body()
        except OverflowError as e:
            self._send_json(413, {"error": str(e)})
            return
        except Exception as e:
            self._send_json(400, {"error": f"Invalid JSON payload: {sanitize_error(e)}"})
            return
        status, data = self.handle_request_dict("POST", self.path, body, headers=dict(self.headers))
        self._send_json(status, data)

    def log_message(self, format, *args):
        return


def run_api_server(host: str = "127.0.0.1", port: int = 8000, config_path: str = "config.yaml", blocking: bool = True):
    CoroVisionRequestHandler.api = CoroVisionAPI(config_path)
    server = HTTPServer((host, port), CoroVisionRequestHandler)
    print(f"\n CoroVision-AI REST API running at http://{host}:{port}/")
    print(" Endpoints: GET /api/health, GET /api/status, GET /api/compare, POST /api/process_case, POST /api/report")

    if blocking:
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            server.server_close()
            print("Server stopped.")
    else:
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        return server, t


if __name__ == "__main__":
    run_api_server("127.0.0.1", 8000, "config.yaml", blocking=True)
