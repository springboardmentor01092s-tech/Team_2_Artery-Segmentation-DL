export type ImageRecord = {
  modality?: string;
  id: string;
  original_name: string;
  width: number;
  height: number;
  spacing_mm: string | null;
  processed_spacing_mm?: string | null;
  roi_box: string | null;
  frame_index: number | null;
  page_index?: number | null;
  latest_analysis_id?: string | null;
  preprocessing: string[];
  processing_record?: {
    pipeline_version?: string;
    profile?: string;
    standard_pipeline?: string | null;
    options?: { denoise?: boolean; contrast_enhancement?: boolean };
    source_sha256?: string;
    processed_sha256?: string;
    warnings?: string[];
  };
  preview_url: string;
  source_url?: string;
};

export type ClinicalReviewRecord = {
  id: string;
  case_id: string;
  reviewer_id: string;
  reviewer_name?: string;
  decision: "approved" | "needs_followup" | "rejected" | "reviewed";
  stenosis_severity: string | null;
  notes: string | null;
  created_at: string;
};

export type CaseRecord = {
  assigned_doctors?: { id: string; name: string; role: string }[];
  id: string;
  owner_id?: string;
  case_code: string;
  patient_code: string | null;
  age_band: string | null;
  gender: string | null;
  medical_history: string[];
  risk_factors: string[];
  clinical_notes: string | null;
  scan_date: string | null;
  modality: string;
  modalities?: string[];
  intended_tasks?: string[];
  processing_routes?: { modality: string; intended_task: string; pipeline: string }[];
  anatomy: string;
  intended_task?: string;
  source_dataset?: string | null;
  source_reference?: string | null;
  clinical_metadata_enabled?: boolean;
  inference_compatible?: boolean;
  status: string;
  workflow_status: string;
  processing_status: string;
  report_status: string;
  report_version: number;
  report_approved_by?: string | null;
  report_approved_at?: string | null;
  permissions?: {
    can_edit: boolean;
    can_upload: boolean;
    can_run_analysis: boolean;
    can_review: boolean;
    can_export: boolean;
    can_assign: boolean;
    can_delete: boolean;
    can_submit_report: boolean;
    can_approve_report: boolean;
  };
  created_at: string;
  reviews?: ClinicalReviewRecord[];
  latest_review?: ClinicalReviewRecord | null;
  report_revisions?: { id: string; version: number; status: string; created_by: string; created_at: string; approved_by: string | null; approved_at: string | null }[];
  comments?: { id: string; user_id: string; body: string; category: string; created_at: string }[];
  images: ImageRecord[];
};

export type AnalysisResult = {
  structured_result?: StructuredResearchResult | null;
  id: string;
  image_id: string;
  model_version: string;
  artery_pixels: number;
  stenosis_pixels: number;
  overlay_url: string;
  attention_map_url?: string;
  stenosis_probability_url?: string;
  gradcam_url?: string;
  centerline_url?: string;
  artery_probability_url?: string;
  model_scores?: {
    artery_foreground_mean_probability?: number | null;
    stenosis_foreground_mean_probability?: number | null;
    calibration?: string;
  };
  validation: Record<string, { validation_dice: number; validation_images: number }>;
  vessel_analysis?: {
    mask_pixels: number;
    centerline_pixels: number;
    centerline_length: number;
    diameter_unit: "px" | "mm";
    mean_diameter: number | null;
    minimum_diameter: number | null;
    diameter_samples: number;
    connected_components: number;
    calibration: string;
    maximum_diameter?: number | null;
    diameter_cv?: number | null;
    boundary_pixels?: number;
    boundary_length?: number;
    branching_points?: number;
    endpoints?: number;
    branch_segments?: number;
    continuity_ratio?: number;
    tortuosity?: number | null;
    cross_section_area?: number;
    cross_section_area_status?: string;
    projected_mask_area?: number;
    area_unit?: string;
    vessel_candidates?: { candidate_id: number; mask_pixels: number; centerline_pixels: number; centerline_length: number; length_unit: string }[];
    branch_points?: { node_id: string; x: number; y: number }[];
    endpoint_points?: { node_id: string; x: number; y: number }[];
    centerline_paths?: { path_id: string; path_type: string; start_node: string | null; end_node: string | null; length: number; length_unit: string; coordinates_xy: [number, number][] }[];
    quality_status?: string;
    quality_flags?: { code: string; severity: "warning" | "review" | "info"; message: string }[];
    stenosis_mask_components?: number;
    stenosis_component_interpretation?: string;
    uncertain_pixel_fraction?: number | null;
    mean_foreground_probability?: number | null;
    threshold_sensitivity?: {
      reference_threshold: number;
      status: string;
      stability_rule?: string;
      evaluations: { threshold: number; mask_dice_vs_selected: number; connected_components: number; centerline_length: number; branch_points: number; endpoints: number; path_count: number }[];
    };
  };
  interpretation: string;
  research_only: boolean;
  created_at: string;
};

export type AnalysisJob = {
  id: string; image_id: string; status: "pending" | "processing" | "completed" | "failed";
  progress: number; error_detail?: string | null; status_url: string; result_url?: string | null;
};

export type StructuredResearchResult = {
  schema_version: string; result_id: string; job_id: string | null;
  stages: Record<string, { status: string; reason: string }>;
  candidates: { candidate_id: string; category_id?: number; model_score?: number;
    bbox_prepared_xyxy?: number[]; bbox_source_xyxy?: number[] | null;
    coordinate_warning?: string | null; association_status?: string }[];
  severity: { status: string; narrowing_percent: number | null; category: string | null; reason: string };
  limitations: string[]; artifacts: Record<string, string>;
  explanation: { version: string; method: string; sections: { title: string; text: string; source_refs: string[] }[] };
};
