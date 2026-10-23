"""Preserved architectures; numerical definitions copied from verified training sources."""
import numpy as np
import torch
from torch import nn
from torchvision.models import resnet34, ResNet34_Weights

def block(a,b):return nn.Sequential(nn.Conv2d(a,b,3,padding=1,bias=False),nn.GroupNorm(8,b),nn.ReLU(),nn.Conv2d(b,b,3,padding=1,bias=False),nn.GroupNorm(8,b),nn.ReLU())

class PretrainedVesselUNet(nn.Module):
    def __init__(self,pretrained=False):
        super().__init__();self.encoder=resnet34(weights=ResNet34_Weights.DEFAULT if pretrained else None);self.d3=block(512+256,256);self.d2=block(256+128,128);self.d1=block(128+64,64);self.d0=block(64+64,32);self.head=nn.Conv2d(32,1,1);self.register_buffer('mean',torch.tensor([.485,.456,.406])[None,:,None,None]);self.register_buffer('std',torch.tensor([.229,.224,.225])[None,:,None,None])
    def forward(self,x):
        size=x.shape[-2:];x=(x.repeat(1,3,1,1)-self.mean)/self.std;e=self.encoder;a=e.relu(e.bn1(e.conv1(x)));b=e.layer1(e.maxpool(a));c=e.layer2(b);d=e.layer3(c);z=e.layer4(d)
        def up(x,y):return torch.cat([nn.functional.interpolate(x,size=y.shape[-2:],mode='bilinear',align_corners=False),y],1)
        z=self.d0(up(self.d1(up(self.d2(up(self.d3(up(z,d)),c)),b)),a))
        return self.head(nn.functional.interpolate(z,size=size,mode='bilinear',align_corners=False))

def build_detector(architecture: str, num_classes: int, pretrained: bool = True):
    from torchvision.models.detection import (MaskRCNN_ResNet50_FPN_Weights,
                                               MaskRCNN_ResNet50_FPN_V2_Weights,
                                               maskrcnn_resnet50_fpn,
                                               maskrcnn_resnet50_fpn_v2)
    from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
    from torchvision.models.detection.mask_rcnn import MaskRCNNPredictor
    if architecture == "maskrcnn_resnet50_fpn_v2":
        model = maskrcnn_resnet50_fpn_v2(weights=MaskRCNN_ResNet50_FPN_V2_Weights.DEFAULT if pretrained else None, weights_backbone=None)
    else:
        model = maskrcnn_resnet50_fpn(weights=MaskRCNN_ResNet50_FPN_Weights.DEFAULT if pretrained else None, weights_backbone=None)
    features = model.roi_heads.box_predictor.cls_score.in_features
    model.roi_heads.box_predictor = FastRCNNPredictor(features, num_classes)
    mask_features = model.roi_heads.mask_predictor.conv5_mask.in_channels
    model.roi_heads.mask_predictor = MaskRCNNPredictor(mask_features, 256, num_classes)
    return model

def mask_to_polygon(mask):
    from cv2 import RETR_EXTERNAL, CHAIN_APPROX_SIMPLE, findContours
    contours, _ = findContours(mask.astype(np.uint8), RETR_EXTERNAL, CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    contour = max(contours, key=lambda c: abs(__import__("cv2").contourArea(c)))
    points = contour.reshape(-1, 2)
    if len(points) < 3:
        return None
    return [(float(x), float(y)) for x, y in points]

def predict_one(model, image, device, score_threshold):
    model.eval()
    with torch.inference_mode():
        out = model([image.to(device)])[0]
    instances = []
    for i, score in enumerate(out["scores"].detach().cpu().numpy()):
        if score < score_threshold:
            continue
        mask_probability = out["masks"][i, 0].detach().cpu().numpy()
        binary = mask_probability >= 0.5
        polygon = mask_to_polygon(binary)
        if polygon is None:
            continue
        instances.append({"category_id": int(out["labels"][i].item()), "score": float(score),
                          "mask_probability": mask_probability, "mask": binary, "polygon": polygon})
    return instances
