"""Experimental source-grid cross-sections on an explicitly associated vessel path.

The caller must resolve saved run identity and verify vessel association. This
module never loads weights, invents references or certifies anatomical validity.
"""
import math
import numpy as np


METHOD_ID = 'source-grid-centerline-diameter-v2'
METHOD_SOURCE = 'Centerline distance-transform widths with nearby-reference comparison'


def candidate_diameters(mask, image, path_xy, candidate_xyxy, *, run_id, candidate_id,
                        association_verified=False, branch_points=(), overlap_known=None,
                        minimum_contrast=0.15, reference_samples=5):
    result=dict(status='abstained', algorithm=METHOD_ID, method_source=METHOD_SOURCE,
        implementation='source-normal-cross-section-v1', run_id=run_id,
        candidate_id=candidate_id, unit='source_px', clinical_validated=False,
        category=None, narrowing_percent=None, reasons=[])
    def abstain(reason):
        return {**result,'reasons':[reason]}
    if not run_id or not candidate_id or association_verified is not True:
        return abstain('candidate_vessel_association_unverified')
    if overlap_known is not False:
        return abstain('vessel_overlap_not_excluded')
    binary=np.asarray(mask); intensity=np.asarray(image,dtype=float)
    if binary.ndim!=2 or intensity.shape!=binary.shape or not np.isfinite(intensity).all():
        return abstain('invalid_source_image_geometry')
    if not np.isin(binary,[0,1]).all() or intensity.min()<0 or intensity.max()>1:
        return abstain('binary_mask_and_normalized_intensity_required')
    binary=binary.astype(bool); path=np.asarray(path_xy,dtype=float)
    box=np.asarray(candidate_xyxy,dtype=float)
    if path.ndim!=2 or path.shape[1]!=2 or len(path)<7 or not np.isfinite(path).all() or box.shape!=(4,) or not np.isfinite(box).all():
        return abstain('invalid_path_or_candidate')
    if box[0]>=box[2] or box[1]>=box[3]:
        return abstain('invalid_candidate_extent')
    if any(box[0]-8<=b[0]<=box[2]+8 and box[1]-8<=b[1]<=box[3]+8 for b in branch_points):
        return abstain('branch_ambiguity_in_candidate_region')
    if np.max(np.linalg.norm(np.diff(path,axis=0),axis=1))>2:
        return abstain('discontinuous_centerline')
    h,w=binary.shape; samples=[]
    for i in range(2,len(path)-2):
        p=path[i]; x,y=map(lambda v:int(round(v)),p)
        if not(0<=x<w and 0<=y<h) or not binary[y,x]:continue
        if any(np.linalg.norm(p-np.asarray(b))<8 for b in branch_points):continue
        tangent=path[i+2]-path[i-2]; length=np.linalg.norm(tangent)
        if length==0:continue
        normal=np.array([-tangent[1],tangent[0]])/length
        boundaries=[]; inside=[]; outside=[]
        for sign in (-1,1):
            last=p
            for distance in np.arange(.5,65,.5):
                q=p+sign*normal*distance; qx,qy=map(lambda v:int(round(v)),q)
                if not(1<=qx<w-1 and 1<=qy<h-1):break
                if not binary[qy,qx]:
                    boundaries.append((last+q)/2);outside.append(intensity[qy,qx]);break
                inside.append(intensity[qy,qx]);last=q
        if len(boundaries)!=2 or not inside:continue
        width=float(np.linalg.norm(boundaries[1]-boundaries[0]))
        contrast=abs(float(np.median(inside))-float(np.mean(outside)))
        samples.append(dict(index=i,point=p.tolist(),endpoints=[q.tolist() for q in boundaries],
            width=width,contrast=contrast,in_lesion=bool(box[0]<=p[0]<=box[2] and box[1]<=p[1]<=box[3])))
    lesion=[s for s in samples if s['in_lesion']]
    if len(lesion)<3:return abstain('insufficient_lesion_cross_sections')
    if min(s['contrast'] for s in lesion)<minimum_contrast:return abstain('low_local_boundary_contrast')
    # Contiguous nearby path window, outside the candidate with a three-sample gap.
    first,last=min(s['index'] for s in lesion),max(s['index'] for s in lesion)
    windows=[]
    for start in range(2,len(path)-reference_samples-2):
        block=[s for s in samples if start<=s['index']<start+reference_samples]
        if len(block)!=reference_samples or any(s['in_lesion'] or s['contrast']<minimum_contrast for s in block):continue
        if not(start+reference_samples<=first-3 or start>=last+3):continue
        widths=[s['width'] for s in block]
        if np.std(widths)/np.mean(widths)>.1:continue
        gap=min(abs(start-first),abs(start-last))
        windows.append((gap,block))
    if not windows:return abstain('no_stable_nearby_reference_segment')
    reference=min(windows,key=lambda item:item[0])[1]
    mld=min(lesion,key=lambda s:s['width']);rvd=float(np.median([s['width'] for s in reference]))
    if mld['width']<=0 or mld['width']>rvd:return abstain('implausible_minimum_reference_relationship')
    return {**result,'status':'experimental_measurement','minimum_diameter':mld['width'],
        'reference_diameter':rvd,'minimum_cross_section':mld,'reference_cross_sections':reference,
        'narrowing_percent':100*(rvd-mld['width'])/rvd,
        'uncertainty_percentage_points':None,
        'limitation':'Predicted-mask research estimate. Uncertainty and independent lumen validation remain unavailable; automatic severity is withheld.'}
