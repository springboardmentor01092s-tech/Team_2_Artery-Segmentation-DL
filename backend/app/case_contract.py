"""Supported research case configurations, not model approval claims."""
from fastapi import HTTPException
import json

TASKS = {"artery_segmentation", "stenosis_localization", "artery_and_stenosis", "volume_preparation"}
ANATOMIES = {"coronary", "aorta", "cerebral", "hepatic"}
MODALITIES = {"XCA", "CT", "CTA", "MRA"}


def validate_case_configuration(modality, anatomy, intended_task):
    task = intended_task
    if modality not in MODALITIES or anatomy not in ANATOMIES or task not in TASKS:
        raise HTTPException(422, "Unsupported modality, anatomy or research task")
    if modality == "XCA":
        if anatomy != "coronary" or task == "volume_preparation":
            raise HTTPException(422, "XCA cases require coronary anatomy and a 2D research task")
    elif task != "volume_preparation":
        raise HTTPException(422, "CT/CTA/MRA currently support volume preparation only, not model inference")


def supports_current_inference(case):
    return "XCA" in case_modalities(case) and case.anatomy == "coronary" and any(task != "volume_preparation" for task in case_tasks(case))


def case_modalities(case):
    return json.loads(getattr(case, "modalities_json", None) or "null") or [case.modality]


def case_tasks(case):
    return json.loads(getattr(case, "intended_tasks_json", None) or "null") or [case.intended_task]


def validate_case_routes(modalities, anatomy, tasks):
    modalities, tasks = list(dict.fromkeys(modalities)), list(dict.fromkeys(tasks))
    if not modalities or not tasks or set(modalities) - MODALITIES or set(tasks) - TASKS or anatomy not in ANATOMIES:
        raise HTTPException(422, "Select at least one supported modality and intended task")
    if "XCA" in modalities and anatomy != "coronary":
        raise HTTPException(422, "Cases containing XCA require coronary anatomy")
    routes = [{"modality": modality, "intended_task": task,
               "pipeline": "xca_2d" if modality == "XCA" else "volume_preparation_export"}
              for modality in modalities for task in tasks
              if (modality == "XCA") == (task != "volume_preparation")]
    if {row["modality"] for row in routes} != set(modalities) or {row["intended_task"] for row in routes} != set(tasks):
        raise HTTPException(422, "XCA needs a 2D research task; CT/CTA/MRA need volume preparation. Every selected option must have a compatible route")
    return modalities, tasks, routes
