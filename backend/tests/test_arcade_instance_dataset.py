import json
from pathlib import Path

import pytest
import torch
from PIL import Image

instance_training = pytest.importorskip("scripts.train_arcade_instances", reason="Training runner belongs to the separate training workspace")


def _write_split(root: Path, task: str, split: str, image_rows, annotations):
    base = root / "arcade" / task / split
    (base / "images").mkdir(parents=True)
    (base / "annotations").mkdir(parents=True)
    for row in image_rows:
        Image.new("RGB", (16, 16), tuple(row.pop("color"))).save(base / "images" / row["file_name"])
    coco = {
        "images": image_rows,
        "annotations": annotations,
        "categories": [{"id": 5, "name": "segment-5"}, {"id": 26, "name": "stenosis"}],
    }
    (base / "annotations" / f"{split}.json").write_text(json.dumps(coco))


def test_instance_dataset_builds_masks_boxes_and_remaps_category_ids(tmp_path, monkeypatch):
    monkeypatch.setattr(instance_training, "ROOT", tmp_path)
    polygon = [2, 2, 9, 2, 9, 9, 2, 9]
    _write_split(
        tmp_path,
        "stenosis",
        "train",
        [{"id": 1, "file_name": "train.png", "width": 16, "height": 16, "color": (100, 100, 100)}],
        [{"id": 10, "image_id": 1, "category_id": 26, "segmentation": [polygon], "iscrowd": 0}],
    )
    _write_split(
        tmp_path,
        "stenosis",
        "val",
        [{"id": 2, "file_name": "val.png", "width": 16, "height": 16, "color": (0, 0, 0)}],
        [],
    )

    dataset = instance_training.ArcadeInstances("stenosis", "train", input_size=16)
    image, target, image_id = dataset[0]

    assert image_id == 1
    assert image.shape == (3, 16, 16)
    assert image.dtype == torch.float32
    assert float(image.min()) >= 0 and float(image.max()) <= 1
    assert target["labels"].tolist() == [1]
    assert target["boxes"].tolist() == [[2.0, 2.0, 10.0, 10.0]]
    assert target["masks"].shape == (1, 16, 16)
    assert int(target["masks"].sum()) == 64


def test_instance_train_dataset_excludes_pixel_duplicate_and_keeps_validation_case(tmp_path, monkeypatch):
    monkeypatch.setattr(instance_training, "ROOT", tmp_path)
    polygon = [2, 2, 9, 2, 9, 9, 2, 9]
    _write_split(
        tmp_path,
        "stenosis",
        "train",
        [
            {"id": 1, "file_name": "duplicate.png", "width": 16, "height": 16, "color": (255, 0, 0)},
            {"id": 2, "file_name": "keep.png", "width": 16, "height": 16, "color": (0, 255, 0)},
        ],
        [{"id": 10, "image_id": 1, "category_id": 26, "segmentation": [polygon], "iscrowd": 0}],
    )
    _write_split(
        tmp_path,
        "stenosis",
        "val",
        [{"id": 3, "file_name": "different-name.png", "width": 16, "height": 16, "color": (255, 0, 0)}],
        [],
    )

    train = instance_training.ArcadeInstances("stenosis", "train", input_size=16)
    validation = instance_training.ArcadeInstances("stenosis", "val", input_size=16)

    assert [row["file_name"] for row in train.images] == ["keep.png"]
    assert train.excluded_train_duplicates == ["duplicate.png"]
    assert [row["file_name"] for row in validation.images] == ["different-name.png"]


def test_missing_shapely_fails_loudly_instead_of_returning_a_fake_zero(monkeypatch):
    if __import__("importlib.util", fromlist=["find_spec"]).find_spec("shapely") is not None:
        pytest.skip("Shapely is installed; missing-dependency behavior is not applicable")

    with pytest.raises(ModuleNotFoundError, match="shapely"):
        instance_training.polygon_f1([(0, 0), (1, 0), (1, 1)], [(0, 0), (1, 0), (1, 1)])


def test_final_evaluation_respects_single_task_candidate(tmp_path, monkeypatch):
    from types import SimpleNamespace
    checkpoint=tmp_path/'syntax'/'mock'/'best.pt'
    checkpoint.parent.mkdir(parents=True)
    checkpoint.touch()
    (tmp_path/'candidate.json').write_text(json.dumps({'architecture':'mock','run_id':'test',
        'tasks':{'syntax':{}},'score_threshold':0.6}))
    calls=[]
    class Model:
        def to(self,device): return self
        def load_state_dict(self,state): pass
    class Test:
        def __init__(self,task,split,size):
            calls.append((task,split))
        def __len__(self): return 3
    monkeypatch.setattr(instance_training.torch,'load',lambda *a,**k:{'num_classes':26,'input_size':512,'state_dict':{}})
    monkeypatch.setattr(instance_training,'build_detector',lambda *a,**k:Model())
    monkeypatch.setattr(instance_training,'ArcadeInstances',Test)
    monkeypatch.setattr(instance_training,'evaluate',lambda model,data,device,score,pixel:{'threshold':score})
    args=SimpleNamespace(output_root=tmp_path,task='syntax',score_threshold=.25,pixel_threshold=.5)
    instance_training.evaluate_candidate_test(args,'cpu')
    report=json.loads((tmp_path/'test_report.json').read_text())
    assert calls==[('syntax','test')]
    assert list(report['final_test_results'])==['syntax']
    assert report['final_test_results']['syntax']['metrics']['threshold']==.6
    with pytest.raises(FileExistsError):
        instance_training.evaluate_candidate_test(args,'cpu')


def test_saved_v1_checkpoint_builder_uses_no_network_and_frozen_norms(monkeypatch):
    pytest.importorskip('torchvision')
    from torchvision.models import _api
    from torchvision.ops.misc import FrozenBatchNorm2d
    def no_download(*args,**kwargs):
        raise AssertionError('Checkpoint evaluation must not download pretrained weights')
    monkeypatch.setattr(_api,'load_state_dict_from_url',no_download)
    model=instance_training.build_detector('maskrcnn_resnet50_fpn',26,pretrained=False)
    assert isinstance(model.backbone.body.bn1,FrozenBatchNorm2d)
    assert model.backbone.body.bn1.eps==0.0
    assert model.roi_heads.box_predictor.cls_score.out_features==26
