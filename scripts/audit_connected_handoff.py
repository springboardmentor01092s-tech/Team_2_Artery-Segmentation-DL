"""Read-only handoff inventory. Does not execute drive code, pool data or train."""
import argparse
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--drive", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    drive = args.drive.resolve()
    package = drive / "CoroVision_Full_20261024"
    manifest = {}
    with (package / "manifest.jsonl").open() as stream:
        for line in stream:
            row = json.loads(line)
            manifest[row["source_path"].replace("\\", "/")] = row

    def resolve(relative):
        row = manifest.get(relative.replace("\\", "/"))
        if not row:
            return None, None
        path = (drive / row["disk_path"]).resolve()
        if not path.is_relative_to(drive):
            raise ValueError("Manifest path escaped drive")
        return path, row

    def metadata(relative):
        path, row = resolve(relative)
        if not path or not path.is_file():
            return {"source": relative, "available": False}
        digest = hashlib.file_digest(path.open("rb"), "sha256").hexdigest()
        return {"source": relative, "available": True, "sha256": digest,
                "manifest_hash_matches": digest == row["sha256"], "disk_path": row["disk_path"]}

    registry_path, _ = resolve("reports/dataset_compatibility/DATASET_REGISTRY.json")
    registry = json.loads(registry_path.read_text())
    hashes_path, _ = resolve("reports/dataset_compatibility/EVIDENCE_HASHES.json")
    evidence = json.loads(hashes_path.read_text())
    verified = []
    for relative, expected in evidence.items():
        result = metadata(relative)
        result["dataset_audit_hash_matches"] = result.get("sha256") == expected
        verified.append(result)
    index_path, _ = resolve("trained_models/index.json")
    index = json.loads(index_path.read_text())
    checkpoints = []
    for task in index["tasks"]:
        for model in task.get("models", []):
            relative = "trained_models/" + task["task"] + "/" + model["checkpoint"].replace("\\", "/")
            path, row = resolve(relative)
            checkpoints.append({"task": task["task"], "relative": relative,
                                "available": bool(path and path.is_file()),
                                "selected_in_source_package": model["selected_for_integration"],
                                "expected_sha256": model["sha256"],
                                "transfer_manifest_sha256": row["sha256"] if row else None,
                                "full_bytes_rehashed": False})
    result = {"scope": "Metadata evidence rehashed; model weights inventoried, not promoted",
              "registry": registry, "evidence": verified, "checkpoints": checkpoints,
              "registry_integrity": metadata("reports/dataset_compatibility/DATASET_REGISTRY.json"),
              "training_changes": False, "pooling_authorized": False}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2))
    print(json.dumps({"datasets": len(registry["datasets"]), "evidence_files": len(verified),
                      "all_evidence_hashes_match": all(r.get("manifest_hash_matches") and r["dataset_audit_hash_matches"] for r in verified),
                      "checkpoints": len(checkpoints), "available": sum(c["available"] for c in checkpoints)}))


if __name__ == "__main__":
    main()
