"""Pinned ImageCAS coarse full-field inference; never used for 2D or other anatomy.

The training arrays were canonical RAS XYZ, despite Torch's conventional DHW
names. Preserve that axis order and the float16 storage round-trip exactly.
"""
import hashlib
import gzip
import math
import os
from pathlib import Path
import threading
import time
import zlib

import nibabel as nib
import numpy as np
from scipy.ndimage import zoom
from nibabel.processing import resample_from_to

MODEL_ID = 'imagecas-coronary-unet3d-128-v1'
CHECKPOINT_SHA = 'b77271b1780f32100bc954ccbec2ac5c4efa54a10e0f5975b631924c8a2f553d'
MAX_VOXELS = 96_000_000
MAX_UPLOAD_BYTES = 384 * 1024 * 1024
MAX_EXPANDED_BYTES = MAX_VOXELS * 8 + 1024 * 1024
# The original acceptance fixture is explicitly synthetic, not a medical study.
SYNTHETIC_FIXTURE_HASHES = {'9ec48d8a037fc283b4d905834d9676eca6c6ac90296405c1200ce119e9a93b1c'}
RUN_LOCK = threading.Lock()
JOB_SLOTS = threading.BoundedSemaphore(2)


def inspect_container(path):
    """Bound the full single-file NIfTI payload before nibabel decodes it.

    The gzip CRC, declared voxel payload, datatype and bit depth are checked.
    Adapted from Team 1's MIT-licensed bounded NIfTI ingestion review.
    """
    path = Path(path)
    header = bytearray()
    expanded = 0
    try:
        stream = gzip.open(path, 'rb') if path.name.lower().endswith('.gz') else path.open('rb')
        with stream:
            while block := stream.read(64 * 1024):
                expanded += len(block)
                if expanded > MAX_EXPANDED_BYTES:
                    raise ValueError('Expanded NIfTI payload exceeds the supported memory limit')
                if len(header) < 540:
                    header.extend(block[:540-len(header)])
    except ValueError:
        raise
    except (OSError, EOFError, zlib.error) as exc:
        raise ValueError('Unreadable or corrupt NIfTI container') from exc
    raw = bytes(header)
    if len(raw) < 348:
        raise ValueError('Truncated NIfTI header')
    try:
        if raw[344:348] == b'n+1\0':
            header_type, header_size = nib.Nifti1Header, 348
        elif len(raw) >= 540 and raw[4:12] == b'n+2\0\r\n\x1a\n':
            header_type, header_size = nib.Nifti2Header, 540
        elif raw[344:348] == b'ni1\0' or raw[4:12] == b'ni2\0\r\n\x1a\n':
            raise ValueError('NIfTI header/image pairs are unsupported; use .nii or .nii.gz')
        else:
            raise ValueError('Invalid single-file NIfTI header')
        parsed = header_type(raw[:header_size], check=False)
        dimensions = int(parsed['dim'][0])
        shape = tuple(int(value) for value in parsed['dim'][1:dimensions+1])
        if dimensions != 3 or len(shape) != 3 or min(shape) < 2 or math.prod(shape) > MAX_VOXELS:
            raise ValueError('Require scalar 3D NIfTI with 2+ voxels per axis, at most 96 million voxels; 4D/time-series are unsupported')
        dtype = np.dtype(parsed.get_data_dtype())
        if dtype.kind not in 'iuf' or int(parsed['bitpix']) != dtype.itemsize * 8:
            raise ValueError('NIfTI datatype and bit depth are unsupported or inconsistent')
        offset = float(parsed['vox_offset'])
        if not math.isfinite(offset) or not offset.is_integer() or offset < header_type.single_vox_offset:
            raise ValueError('Invalid NIfTI voxel payload offset')
        expected = int(offset) + math.prod(shape) * dtype.itemsize
        if expected > MAX_EXPANDED_BYTES:
            raise ValueError('Declared NIfTI payload exceeds the supported memory limit')
        if expanded < expected:
            raise ValueError('Truncated NIfTI voxel payload')
    except ValueError:
        raise
    except (KeyError, OverflowError, TypeError, nib.spatialimages.HeaderDataError) as exc:
        raise ValueError('NIfTI header could not be interpreted safely') from exc
    return {'shape': shape, 'dtype': dtype.name, 'expanded_bytes': expanded}


def checkpoint_path():
    return Path(os.getenv('COROVISION_3D_CHECKPOINT', Path(__file__).resolve().parents[2] / 'models' / 'volume_release' / 'imagecas128.pt'))


def model_status(model_key='imagecas'):
    from .task_models import SPECS,installed
    spec=SPECS[model_key]
    if spec['kind']!='volume':raise ValueError('Not a volume task')
    return {'model_id': MODEL_ID if model_key=='imagecas' else model_key+'-unet3d-128-v1', 'model_key':model_key,'installed':installed(model_key),
            'title':spec['title'],'modality': 'CT/CTA' if model_key=='aorta_aligned' else 'CTA', 'anatomy': spec['anatomy'], 'resolution': [128]*3,
            'approval': 'research_only', 'clinical_validated': False,
            'limits': {'max_file_bytes': MAX_UPLOAD_BYTES, 'max_source_voxels': MAX_VOXELS},
            'limitations': ['Coarse full-field model; small vessels can be lost.',
                            'No 3D stenosis, severity or validated physical diameter estimation.']}


def build_model():
    import torch
    from torch import nn

    def block(a, b):
        return nn.Sequential(nn.Conv3d(a, b, 3, padding=1, bias=False), nn.GroupNorm(4, b),
                             nn.LeakyReLU(.1), nn.Conv3d(b, b, 3, padding=1, bias=False),
                             nn.GroupNorm(4, b), nn.LeakyReLU(.1))

    class UNet3D(nn.Module):
        def __init__(self):
            super().__init__()
            w = 12
            self.enc = nn.ModuleList([block(1,w), block(w,w*2), block(w*2,w*4), block(w*4,w*8)])
            self.pool = nn.MaxPool3d(2)
            self.up = nn.ModuleList([nn.ConvTranspose3d(w*8,w*4,2,2), nn.ConvTranspose3d(w*4,w*2,2,2), nn.ConvTranspose3d(w*2,w,2,2)])
            self.dec = nn.ModuleList([block(w*8,w*4), block(w*4,w*2), block(w*2,w)])
            self.head = nn.Conv3d(w,2,1)

        def forward(self, x):
            skip = []
            for i, encoder in enumerate(self.enc):
                x = encoder(x)
                if i < 3:
                    skip.append(x)
                    x = self.pool(x)
            for up, decoder, s in zip(self.up, self.dec, reversed(skip)):
                x = decoder(torch.cat([up(x), s], 1))
            return self.head(x)

    return UNet3D()


def inspect_input(path):
    """Bound memory from the NIfTI header before decoding any native voxel array."""
    inspect_container(path)
    try:
        image = nib.load(str(path))
    except (OSError, ValueError, nib.filebasedimages.ImageFileError) as exc:
        raise ValueError('Unreadable NIfTI file; use an intact .nii or .nii.gz volume') from exc
    if not isinstance(image, (nib.Nifti1Image, nib.Nifti2Image)) or image.get_data_dtype().kind not in 'iuf':
        raise ValueError('Require scalar numeric CT data; colour, complex and vector inputs are unsupported')
    if len(image.shape) != 3 or min(image.shape) < 2 or math.prod(image.shape) > MAX_VOXELS:
        raise ValueError('Require scalar 3D NIfTI with 2+ voxels per axis, at most 96 million voxels; 4D/time-series are unsupported')
    if image.header.get_xyzt_units()[0] != 'mm':
        raise ValueError('NIfTI spatial units must explicitly be millimetres')
    if not np.isfinite(image.affine).all() or abs(np.linalg.det(image.affine[:3,:3])) < 1e-9:
        raise ValueError('Invalid source physical affine')
    return image


def prepare_input(path):
    image = inspect_input(path)
    canonical = nib.as_closest_canonical(image)
    values = np.array(canonical.dataobj, dtype=np.float32, copy=True)
    if not np.isfinite(values).all():
        raise ValueError('Non-finite CT intensities')
    # Exact source prepare_imagecas_streaming.py, including float16 NPZ storage.
    np.clip(values, -200, 800, out=values)  # Owned array only; never mutate the source.
    prepared = ((zoom(values, np.array([128]*3)/values.shape,
                      order=1, prefilter=False) + 200)/1000).astype(np.float16).astype(np.float32)
    coarse_affine = canonical.affine @ np.diag([*( (np.array(canonical.shape)-1)/127 ), 1.])
    return image, canonical, prepared, coarse_affine


def restore_mask(mask, coarse_affine, source):
    # scipy.zoom grid_mode=False preserves first/last voxel centres.
    coarse = nib.Nifti1Image(mask.astype(np.uint8), coarse_affine)
    restored = resample_from_to(coarse, (source.shape, source.affine), order=0, mode='nearest')
    result = nib.Nifti1Image(np.asarray(restored.dataobj, dtype=np.uint8), source.affine)
    result.header.set_xyzt_units('mm')
    result.set_qform(source.get_qform(), int(source.header['qform_code']))
    result.set_sform(source.get_sform(), int(source.header['sform_code']))
    return result


def run_inference(source_path, output, model_key='imagecas'):
    import torch
    from PIL import Image
    started = time.monotonic()
    torch.set_num_threads(2)
    from .task_models import SPECS,checkpoint_path as task_path
    spec=SPECS[model_key]
    if spec['kind']!='volume':raise ValueError('Not a volume task')
    path = checkpoint_path() if model_key=='imagecas' else task_path(model_key)
    if not path.is_file():
        raise ValueError('Pinned 3D checkpoint is not installed')
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != (CHECKPOINT_SHA if model_key=='imagecas' else spec['sha256']):
        raise ValueError('3D checkpoint checksum mismatch; refusing an unregistered model')
    source, canonical, prepared, coarse_affine = prepare_input(source_path)
    checkpoint = torch.load(path, map_location='cpu', weights_only=True)
    if (checkpoint['manifest']['labels'] != {'0':'background','1':spec['label']}
            or checkpoint['manifest'].get('resolution',[128]*3) != [128]*3):
        raise ValueError('Checkpoint class mapping mismatch')
    model = build_model()
    model.load_state_dict(checkpoint['model'], strict=True)
    model.eval()
    with torch.inference_mode():
        logits = model(torch.from_numpy(prepared)[None,None])
        if logits.shape != (1,2,128,128,128) or not torch.isfinite(logits).all():
            raise ValueError('Invalid model output')
        probability = logits.softmax(1)[0,1].numpy()
        mask = logits.argmax(1)[0].numpy().astype(np.uint8)
    output.mkdir(parents=True, exist_ok=True)
    restored = restore_mask(mask, coarse_affine, source)
    nib.save(restored, output/'mask_source.nii.gz')
    coarse = nib.Nifti1Image(probability, coarse_affine)
    coarse.header.set_xyzt_units('mm')
    nib.save(coarse, output/'probability_coarse.nii.gz')
    # Orthogonal canonical-RAS slice views; orientation explicit, no anatomical labels.
    slices = []
    for axis in range(3):
        index = 64
        gray = np.uint8(np.take(prepared,index,axis=axis).T[::-1]*255)
        selected = np.take(mask,index,axis=axis).T[::-1].astype(bool)
        rgb = np.repeat(gray[...,None],3,axis=2)
        rgb[selected] = (rgb[selected]*.45 + np.array([0,210,170])*.55).astype(np.uint8)
        name = f'overlay_{axis}.png'
        Image.fromarray(rgb).save(output/name)
        slices.append({'axis': ['RAS X','RAS Y','RAS Z'][axis], 'coarse_index': index, 'artifact': name})
    return {'schema_version':'volume-analysis-1.0', 'model_id':MODEL_ID if model_key=='imagecas' else model_key+'-unet3d-128-v1','model_key':model_key,'anatomy':spec['anatomy'],
            'checkpoint_sha256':digest, 'checkpoint_epoch':int(checkpoint['epoch']),
            'preprocessing': {'version':'imagecas-source-parity-1', 'axis_order':'canonical RAS XYZ',
                              'clip_hu':[-200,800], 'normalization':'(clip+200)/1000',
                              'resize':'scipy zoom order=1 prefilter=False grid_mode=False',
                              'float16_storage_roundtrip':True, 'shape':[128]*3},
            'source_shape':list(source.shape), 'source_affine_ras_mm':source.affine.tolist(),
            'canonical_shape':list(canonical.shape), 'coarse_affine_ras_mm':coarse_affine.tolist(),
            'coarse_foreground_voxels':int(mask.sum()),
            'source_grid_foreground_voxels':int(np.asarray(restored.dataobj).sum()),
            'duration_seconds':round(time.monotonic()-started,3), 'device':'cpu',
            'slices':slices, 'clinical_validated':False, 'severity':None,
            'limitations':model_status(model_key)['limitations'] + (["Aorta training references were AI pseudo-labels; only 12 aligned source pairs."] if model_key=='aorta_aligned' else []) + [
                'Resampling a coarse mask onto source geometry does not recover native-resolution vessel detail.',
                'Probabilities are uncalibrated model outputs, not diagnostic confidence.',
                'No overlap/performance metric is calculated without a matching reference mask.']}
