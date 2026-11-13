"""Frozen-artifact geometry integration; no model execution or weight loading."""
import json
import numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation, binary_erosion, label
from .analysis_model import analyze_vessel_geometry
from .local_diameters import METHOD_ID, METHOD_SOURCE, candidate_diameters
from .narrowing import experimental_research_grade


def source_mask(image, mask_path):
    with Image.open(image.original_path) as original:
        gray=np.asarray(original.convert('L'),dtype=float)/255
    with Image.open(mask_path) as source:
        prepared=source.convert('L')
        config=json.loads(image.preprocessing_config_json or '{}')
        geometry=config.get('resize_geometry')
        if geometry:
            left,top=geometry['padding_left_top_xy'];cw,ch=geometry['content_size_xy']
            sx,sy=geometry['source_pixels_per_content_pixel_xy'];ox,oy=geometry['source_roi_origin_xy']
            if any(float(v)!=int(v) for v in (left,top,cw,ch,ox,oy)):
                raise ValueError('Noninteger source ROI geometry unsupported')
            if min(left,top,ox,oy)<0 or min(cw,ch,sx,sy)<=0 or left+cw>prepared.width or top+ch>prepared.height:
                raise ValueError('Invalid saved resize geometry')
            rw,rh=round(cw*sx),round(ch*sy)
            if ox+rw>gray.shape[1] or oy+rh>gray.shape[0]:raise ValueError('Source ROI exceeds original image')
            roi=prepared.crop((left,top,left+cw,top+ch)).resize((rw,rh),Image.Resampling.NEAREST)
            mask=np.zeros(gray.shape,bool);mask[int(oy):int(oy)+rh,int(ox):int(ox)+rw]=np.asarray(roi)>0
        elif prepared.size==(gray.shape[1],gray.shape[0]):
            mask=np.asarray(prepared)>0
        else:raise ValueError('Missing inverse resize geometry')
    if gray.shape!=(image.height,image.width):raise ValueError('Original image dimensions differ from saved record')
    return mask,gray


def measure_candidate(mask, gray, candidate, run_id, authorization=None):
    base=dict(candidate_id=candidate['candidate_id'],candidate=candidate,status='abstained',
        minimum_diameter=None,reference_diameter=None,narrowing_percent=None,unit='source_px',
        reasons=[],severity=dict(status='indeterminate',category=None,reason='Measurement unavailable'))
    def stop(reason):return {**base,'reasons':[reason]}
    box=candidate.get('bbox_source_xyxy')
    if not box or candidate.get('coordinate_warning'):return stop('original_coordinate_mapping_unreliable')
    x1,y1,x2,y2=box
    if not(0<=x1<x2<=mask.shape[1] and 0<=y1<y2<=mask.shape[0]):return stop('candidate_outside_original_image')
    geometry=analyze_vessel_geometry(mask)
    branches=[(p['x'],p['y']) for p in geometry['branch_points']]
    paths=[]
    for path in geometry['centerline_paths']:
        points=path['coordinates_xy']
        count=sum(x1<=x<x2 and y1<=y<y2 for x,y in points)
        if path['path_type']=='centerline' and count>=3:paths.append((path,count))
    if len(paths)!=1:return stop('ambiguous_vessel_paths' if paths else 'no_candidate_crossing_centerline')
    path=paths[0][0];components,_=label(mask)
    component_ids={int(components[y,x]) for x,y in path['coordinates_xy'] if x1<=x<x2 and y1<=y<y2}
    if len(component_ids)!=1 or 0 in component_ids:return stop('disconnected_vessel_association')
    # Multiple disconnected vessels within the box are ambiguous even if only
    # one yielded a sufficiently long skeleton path.
    roi=components[int(y1):int(np.ceil(y2)),int(x1):int(np.ceil(x2))]
    counts=np.bincount(roi.ravel()); substantial=[i for i,n in enumerate(counts) if i and n>=3]
    if len(substantial)!=1:return stop('multiple_vessel_components_in_candidate')
    args=dict(image=gray,path_xy=path['coordinates_xy'],candidate_xyxy=box,
        run_id=run_id,candidate_id=candidate['candidate_id'],association_verified=True,
        overlap_known=False,branch_points=branches)
    nominal=candidate_diameters(mask,**args)
    result={**base,**nominal,'candidate':candidate,
        'measurement_method':dict(id=METHOD_ID, source=METHOD_SOURCE,
            adaptation='Original predicted-mask width comparison strengthened with source-grid cross-sections, unique-path association, branch exclusion, local contrast, stable nearby reference selection and boundary sensitivity.'),
        'association':dict(status='unique_geometric_path',path_id=path['path_id'],
            component_id=next(iter(component_ids)),inside_samples=paths[0][1],
            anatomical_identity_verified=False,overlap_assessment='mask_topology_screen_only'),
        'width_profile_path_xy':path['coordinates_xy']}
    if nominal['status']!='experimental_measurement':return result
    if nominal['narrowing_percent']==0:
        # A candidate box can truncate the lesion, leaving a purported nearby
        # reference on the same narrowed plateau. Equal widths cannot establish
        # a negative/normal segment without independent reference review.
        return {**result,'status':'abstained','narrowing_percent':None,
            'reasons':['reference_suitability_unconfirmed_equal_widths']}
    variants=[]
    for name,perturbed in [('erode_one_source_pixel',binary_erosion(mask)),('dilate_one_source_pixel',binary_dilation(mask))]:
        # Contrast eligibility is assessed on the nominal image/mask boundary.
        # Perturbations move the mask only, so reusing their displaced boundary
        # as a fresh contrast test would confound geometry and image eligibility.
        value=candidate_diameters(perturbed,minimum_contrast=0,**args)
        variants.append(dict(perturbation=name,result=value))
    sensitivity=dict(method='source-mask-morphology-v1',radius_source_px=1,
        statistical_confidence_interval=False,variants=variants)
    if any(v['result']['status']!='experimental_measurement' for v in variants):
        result.update(status='abstained',narrowing_percent=None,reasons=['boundary_sensitivity_measurement_failed'])
        result['sensitivity']=sensitivity
        return result
    values=[nominal['narrowing_percent']]+[v['result']['narrowing_percent'] for v in variants]
    low,high=min(values),max(values)
    uncertainty=max(nominal['narrowing_percent']-low,high-nominal['narrowing_percent'])
    sensitivity.update(narrowing_range_percentage_points=[low,high],max_deviation_percentage_points=uncertainty)
    result['sensitivity']=sensitivity;result['uncertainty_percentage_points']=uncertainty
    result['severity']=experimental_research_grade(nominal['narrowing_percent'],authorization=authorization,
        uncertainty_percentage_points=uncertainty)
    return result
