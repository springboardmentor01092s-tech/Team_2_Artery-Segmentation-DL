// Shared fake data for the frontend tests.

export const CASES = [
  {
    id: 1,
    patient_id: 'p001',
    age: 20,
    gender: 'Female',
    imaging_modality: 'Coronary angiography',
    anatomical_region: 'LAD',
    scan_date: '2026-10-24',
    image_path: 'case_1_scan.png',
    analysis_status: 'Stenosis pipeline complete',
  },
  {
    id: 2,
    patient_id: 'p002',
    age: 21,
    gender: 'Male',
    imaging_modality: 'Coronary angiography',
    anatomical_region: 'LAD',
    scan_date: '2026-10-12',
    image_path: null,
    analysis_status: 'Pending',
  },
];

export const METRICS = {
  n_test: 1156,
  accuracy: 0.863,
  precision: 0.742,
  recall: 0.907,
  specificity: 0.842,
  f1: 0.816,
  auc: 0.931,
  tp: 350,
  fp: 122,
  tn: 648,
  fn: 36,
};

export const COMPARISON = {
  note: 'Test-set results.',
  models: [
    { name: 'U-Net (artery)', task: 'syntax', dice: 0.7597, iou: 0.6126, precision: 0.7788, recall: 0.7416 },
    { name: 'Attention U-Net (artery)', task: 'syntax', dice: 0.7509, iou: 0.6012, precision: 0.7792, recall: 0.7246 },
    { name: 'U-Net (stenosis)', task: 'stenosis', dice: 0.4888, iou: 0.3235, precision: 0.5159, recall: 0.4644 },
    { name: 'Attention U-Net (stenosis)', task: 'stenosis', dice: 0.478, iou: 0.3142, precision: 0.4805, recall: 0.4759 },
  ],
};

export const PIPELINE = {
  model_version: 'unet-artery-v1',
  stages_done: [
    'artery_segmentation',
    'stenosis_segmentation',
    'vessel_analysis',
    'candidate_extraction',
    'stenosis_classification',
    'stenosis_localization',
    'narrowing_estimation',
    'severity_classification',
    'explainable_ai',
    'visualization',
  ],
  vessel_stats: {
    vessel_segments: 2,
    centerline_length_px: 776,
    mean_diameter_px: 15.45,
    max_diameter_px: 26,
    min_diameter_px: 10,
  },
  vessel_mask_url: '/uploads/results/m.png',
  centerline_url: '/uploads/results/c.png',
  stenosis_mask_url: '/uploads/results/s.png',
  visualization_url: '/uploads/results/v.png',
  candidates: [
    {
      score: 0.972,
      bbox: [10, 10, 20, 20],
      location: 'middle-center',
      segment: 1,
      narrowing_pct: 26.5,
      severity: 'mild',
      narrowest_width_px: 15.6,
      reference_width_px: 21.3,
      gradcam_url: '/uploads/results/g1.png',
    },
    {
      score: 0.738,
      bbox: [40, 40, 20, 20],
      location: 'upper-center',
      segment: 1,
      narrowing_pct: 54.5,
      severity: 'moderate',
      narrowest_width_px: 10,
      reference_width_px: 22,
      gradcam_url: '/uploads/results/g2.png',
    },
  ],
};

/** Builds a fake api.get that answers like the backend. */
export function makeGet({ role = 'clinician', cases = CASES, summary = { 1: ['syntax', 'stenosis'] } } = {}) {
  return async (url) => {
    switch (url) {
      case '/auth/me':
        return { data: { id: 1, name: 'Test User', email: 'test@example.com', role } };
      case '/cases':
        return { data: cases };
      case '/cases/results/summary':
        return { data: summary };
      case '/cases/model-metrics':
        return { data: METRICS };
      case '/cases/model-comparison':
        return { data: COMPARISON };
      default:
        if (/^\/cases\/\d+\/results$/.test(url)) return { data: {} };
        if (/^\/cases\/\d+\/report$/.test(url)) return { data: new Blob(['report']) };
        throw { response: { status: 404 } };
    }
  };
}