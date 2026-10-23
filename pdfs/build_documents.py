import os
from pdf_engine import PDFDocument

def generate_project_documentation(filepath):
    doc = PDFDocument(
        filename=filepath,
        title="Project Documentation",
        page_width=595.28,
        page_height=841.89
    )

    # Title
    doc.add_main_title(
        title="Artery Segmentation and Stenosis Detection using Advanced Deep Learning Techniques",
        doc_type="Project Documentation"
    )

    # 1. Objectives
    doc.add_section_header("1. Project Objectives")
    doc.add_paragraph(
        "The primary objective of this project is to develop an automated, clinically reliable deep learning framework for accurate coronary artery segmentation and quantitative stenosis detection from medical angiographic images. Specifically, the system aims to:"
    )
    doc.add_bullet("Artery Segmentation:", "Accurately delineate the lumen boundaries of coronary arteries in medical angiographic images, addressing challenges such as low contrast, vessel overlap, and background noise.")
    doc.add_bullet("Centerline Extraction:", "Extract continuous anatomical vessel centerlines to compute local cross-sectional diameters along the arterial tree.")
    doc.add_bullet("Stenosis Detection & Localization:", "Automatically detect, locate, and assess regions of arterial narrowing (stenosis) across major coronary branches.")
    doc.add_bullet("Quantitative Severity Grading:", "Calculate the percentage of diameter and area reduction (stenosis percentage) to determine lesion severity according to standard clinical criteria.")

    # 2. Workflow & Preprocessing Pipeline
    doc.add_section_header("2. Workflow & Initial Preprocessing Pipeline")
    doc.add_paragraph(
        "The project follows a structured sequential workflow from raw image acquisition to clinical diagnostic output:"
    )
    doc.add_bullet("Step 1: Data Preprocessing:", "Image normalization, contrast enhancement (CLAHE), noise reduction, and region-of-interest (ROI) extraction from input angiographic scans.")
    doc.add_bullet("Step 2: Vessel Segmentation:", "Feeding preprocessed images into a deep learning segmentation model to generate binary/probability masks of the coronary arterial tree.")
    doc.add_bullet("Step 3: Centerline & Diameter Profiling:", "Morphological skeletonization of the predicted mask, curve smoothing, and orthogonal diameter calculation along the vessel length.")
    doc.add_bullet("Step 4: Stenosis Detection & Quantification:", "Identifying the minimal lumen diameter (MLD) relative to the reference healthy vessel diameter (RVD) to compute percentage stenosis: Stenosis % = (1 - MLD / RVD) * 100.")
    doc.add_bullet("Step 5: Output & Reporting:", "Visualizing segmented arteries, overlaying detected stenosis regions, and generating quantitative diagnostic metrics.")

    doc.add_subsection_header("Initial Preprocessing Pipeline Details")
    doc.add_bullet("Intensity Normalization:", "Scaling raw pixel intensities to [0, 1] range and handling bit-depth variations (8-bit vs 12/16-bit DICOM).")
    doc.add_bullet("Contrast Enhancement (CLAHE):", "Contrast Limited Adaptive Histogram Equalization applied locally to boost low-contrast vessel contours without amplifying background noise.")
    doc.add_bullet("Vesselness Filtering:", "Multi-scale Frangi/Hessian filtering to enhance tubular vascular structures and suppress non-vascular planar artifacts.")
    doc.add_bullet("Format Conversion & Resizing:", "Standardizing multi-format inputs (DICOM, NIfTI, PNG, JPG) to uniform resolution (512x512) with isotropic spacing.")

    # 3. Modality, Dataset & Exploratory Data Analysis
    doc.add_section_header("3. Imaging Modality, Dataset & Exploratory Data Analysis")
    doc.add_bullet("Medical Imaging Modality:", "Selected 2D X-ray Coronary Angiography (XCA) as the primary interventional modality for real-time cath-lab assessment, with complementary support for 3D Coronary Computed Tomography Angiography (CCTA).")
    doc.add_bullet("Public / De-identified Datasets:", "Selected and downloaded benchmark datasets: DCA1 (130 coronary angiograms with lumen masks), ARCADE (1,200 multi-view series with vessel tree and stenosis annotations), and ASOCA (40 3D CCTA volumes).")
    doc.add_bullet("Dataset Structure & Annotations:", "Hierarchical directory structure containing raw images, expert-annotated binary lumen masks (0: background, 1/255: lumen), and stenosis metadata (bounding boxes, MLD, and % narrowing).")
    doc.add_bullet("Exploratory Data Analysis (EDA):", "Identified key data characteristics: severe foreground-to-background class imbalance (vessels occupy < 6% of pixels), non-uniform contrast agent distribution across cardiac phases, catheter occlusions, and patient respiratory motion artifacts.")

    # 4. Architecture & System Implementation
    doc.add_section_header("4. Architecture & Full-Stack System Implementation")
    doc.add_subsection_header("Deep Learning Model Architecture")
    doc.add_bullet("Model Backbone:", "Attention U-Net encoder-decoder network with multi-scale convolutional feature extraction layers.")
    doc.add_bullet("Attention Mechanism:", "Attention gates integrated into skip connections to prioritize vascular boundaries and suppress background tissue noise.")
    doc.add_bullet("Loss Optimization:", "Compound loss combining Focal Loss and Soft Dice Loss to resolve high foreground-background class imbalance.")

    doc.add_subsection_header("Full-Stack System Architecture")
    doc.add_bullet("Frontend:", "React, TypeScript, and Vite providing a responsive, interactive clinical dashboard.")
    doc.add_bullet("Backend:", "FastAPI asynchronous REST API handling authentication, case lifecycle, upload handling, and analysis orchestration.")
    doc.add_bullet("Database:", "PostgreSQL storing users, cases, images, preprocessing runs, analyses, findings, and audit logs.")
    doc.add_bullet("Storage:", "Encrypted file storage for original uploads, processed tensors, segmentation masks, overlays, and model weights.")
    doc.add_bullet("AI Services:", "Decoupled inference services hosting separate models for 2D X-ray Angiography and 3D CT/CTA pipelines via a Model Registry.")

    doc.add_subsection_header("Core Software Modules & Implementation")
    doc.add_bullet("Authentication Module:", "Secure user authentication using JWT sessions, password hashing (bcrypt), session expiration, and role-based access checks.")
    doc.add_bullet("Case Management Module:", "Comprehensive case lifecycle management (creation, patient code assignment, modality specification, status transitions, and team access).")
    doc.add_bullet("Image Upload Module:", "Secure file upload supporting drag-and-drop for multi-format medical imaging (DICOM, PNG, JPG, NIfTI, PDF) with validation and preprocessing triggers.")

    doc.add_subsection_header("Database Schema")
    widths = [110, 220, 169]
    doc.add_table_row(["Table", "Main Fields", "Purpose"], widths=widths, is_header=True)
    doc.add_table_row(["users", "id, email, username, password_hash, role, status", "User identity and role"], widths=widths)
    doc.add_table_row(["user_profiles", "user_id, display_name, organisation", "Profile details"], widths=widths)
    doc.add_table_row(["auth_sessions", "id, user_id, expires_at, revoked_at", "Remembered and active sessions"], widths=widths)
    doc.add_table_row(["audit_events", "id, user_id, action, metadata, created_at", "Security and activity tracking"], widths=widths)
    doc.add_table_row(["patients", "id, patient_code, age_range, gender, risk_factors", "De-identified patient details"], widths=widths)
    doc.add_table_row(["cases", "id, case_code, patient_id, modality, anatomy, status", "Imaging case record"], widths=widths)
    doc.add_table_row(["case_assignments", "case_id, user_id, permission", "Team access to a case"], widths=widths)
    doc.add_table_row(["medical_images", "id, case_id, source_path, format, spacing", "Uploaded images and studies"], widths=widths)
    doc.add_table_row(["preprocessing_runs", "id, image_id, settings, output_path, status", "Normalization & conversion history"], widths=widths)
    doc.add_table_row(["analysis_runs", "id, image_id, model_id, task, status, confidence", "Each AI analysis execution"], widths=widths)
    doc.add_table_row(["analysis_findings", "id, analysis_id, type, location, severity, confidence", "Vessel or stenosis findings"], widths=widths)
    doc.add_table_row(["model_versions", "id, name, version, modality, task, metrics, status", "Registered models & validation metrics"], widths=widths)
    doc.add_table_row(["reports", "id, case_id, analysis_id, format, file_path", "Generated PDF, JSON, CSV reports"], widths=widths)
    doc.add_table_row(["notifications", "id, user_id, case_id, level, message, read_at", "Alerts for stenosis or failures"], widths=widths)

    doc.add_subsection_header("UI Wireframes & Role-Based Access Control (RBAC)")
    doc.add_bullet("1. Login Screen:", "Secure sign-in with email/password, social auth, and role switcher (Clinician, Researcher, ML Engineer).")
    doc.add_bullet("2. Main Dashboard:", "Navigation sidebar, summary counters (Total cases, In review, Alerts), and recent cases table.")
    doc.add_bullet("3. Case & Upload Screen:", "Form for Case ID, Modality (X-ray/CT/CTA), de-identified Patient Code, risk factors, drag-and-drop file upload, and preprocessing settings.")
    doc.add_bullet("4. Analysis Workspace:", "Interactive comparison viewer (Original image, Vessel mask, Stenosis overlay), centerline & diameter profile plots, confidence scores, and diagnostic findings.")
    
    rbac_w = [140, 359]
    doc.add_table_row(["Role", "Main Access Permissions"], widths=rbac_w, is_header=True)
    doc.add_table_row(["Radiologist / Clinician", "Review cases, view findings, add clinical comments, export reports"], widths=rbac_w)
    doc.add_table_row(["Medical Researcher", "Upload de-identified data, compare analyses, export research data"], widths=rbac_w)
    doc.add_table_row(["ML Engineer", "Dataset audit, preprocessing, training records, model registry management"], widths=rbac_w)
    doc.add_table_row(["Administrator", "User & role management, audit logs, system settings, deleted-case recovery"], widths=rbac_w)

    doc.save()


def generate_daily_work_log(filepath):
    doc = PDFDocument(
        filename=filepath,
        title="Daily Project Work Log",
        page_width=595.28,
        page_height=841.89
    )

    # Title
    doc.add_main_title(
        title="Artery Segmentation and Stenosis Detection using Advanced Deep Learning Techniques",
        doc_type="Daily Project Work Log"
    )

    # 1. Objective
    doc.add_section_header("Objective")
    doc.add_paragraph(
        "To develop an automated deep learning framework for accurate coronary artery lumen segmentation, centerline extraction, and quantitative stenosis detection and severity grading from angiographic images."
    )

    # 2. Workflow
    doc.add_section_header("Workflow")
    doc.add_bullet("Step 1: Data Preprocessing:", "Input image normalization, contrast enhancement (CLAHE), and noise suppression.")
    doc.add_bullet("Step 2: Artery Segmentation:", "Deep learning model prediction of arterial lumen masks.")
    doc.add_bullet("Step 3: Centerline & Geometry Profiling:", "Skeletonization and orthogonal diameter measurement across the vessel path.")
    doc.add_bullet("Step 4: Stenosis Quantification:", "Local minimal lumen diameter calculation and percentage narrowing determination.")
    doc.add_bullet("Step 5: Visualization & Output:", "Visual overlay of segmented vessels and quantified stenosis findings.")

    # 3. Architecture
    doc.add_section_header("Architecture")
    doc.add_bullet("Model Architecture:", "Attention U-Net / U-Net encoder-decoder network with multi-scale convolution and compound Focal + Soft Dice loss.")
    doc.add_bullet("System Platform:", "FastAPI backend, React + TypeScript UI, PostgreSQL database, secure file storage, and dedicated AI inference pipelines for X-ray and CT/CTA.")

    # 4. About It / Daily Work Done
    doc.add_section_header("About It (Daily Work Done)")
    
    # October 8, 2026
    doc.add_subsection_header("October 8, 2026")
    doc.add_bullet("Define Project Objectives & Workflow:", "Formalized core objectives for lumen segmentation, centerline extraction, and stenosis severity quantification; established 5-step sequential workflow.")
    doc.add_bullet("Architecture Selection:", "Specified Attention U-Net network backbone and compound Focal + Soft Dice loss formulation.")
    doc.add_bullet("Documentation Setup:", "Established project documentation structure and automated black-and-white PDF reporting system.")

    # October 9, 2026
    doc.add_subsection_header("October 9, 2026")
    doc.add_bullet("Select Medical Imaging Modality:", "Selected 2D X-ray Coronary Angiography (XCA) as primary modality and 3D CCTA as complementary modality.")
    doc.add_bullet("Select & Download Appropriate Dataset:", "Acquired public/de-identified benchmark datasets (DCA1, ARCADE, ASOCA) for vascular segmentation and stenosis evaluation.")
    doc.add_bullet("Understand Dataset Structure & Annotations:", "Analyzed directory structure, image resolutions, binary lumen masks, and clinical stenosis bounding box annotations.")

    # October 12, 2026
    doc.add_subsection_header("October 12, 2026")
    doc.add_bullet("Design System Architecture:", "Designed full-stack system architecture comprising React + TypeScript UI, FastAPI REST API, PostgreSQL database, secure storage, and decoupled AI services.")
    doc.add_bullet("Design Database Schema:", "Specified 14 relational tables covering users, patients, cases, images, preprocessing, analyses, findings, models, and reports.")
    doc.add_bullet("Create UI Wireframes:", "Designed wireframes for Login, Main Dashboard, Case & Upload Screen, Analysis Workspace, and Role-Based Access Control (RBAC).")

    # October 15, 2026 (Today)
    doc.add_subsection_header("October 15, 2026 (Today's Work)")
    doc.add_bullet("Perform Exploratory Data Analysis:", "Conducted EDA on angiographic images: evaluated intensity distribution, contrast variability, vascular pixel sparsity (<6%), and catheter/motion artifacts.")
    doc.add_bullet("Set Up Frontend and Backend:", "Initialized full-stack project scaffolds with React, TypeScript, and Vite on frontend, and FastAPI with modular API routing on backend.")
    doc.add_bullet("Implement Authentication:", "Built user authentication module with password hashing, JWT session token generation, session expiration, and role verification.")
    doc.add_bullet("Implement Case Management:", "Built case management service handling case creation, patient code linkage, modality tagging, status progression, and team access permissions.")
    doc.add_bullet("Implement Image Upload:", "Implemented multi-format file upload endpoint supporting DICOM, PNG, JPG, and NIfTI with file integrity verification and secure directory storage.")
    doc.add_bullet("Build Initial Preprocessing Pipeline:", "Constructed initial image preprocessing pipeline implementing intensity normalization, CLAHE contrast enhancement, and noise filtering.")

    doc.save()


if __name__ == "__main__":
    out_dir = os.path.dirname(os.path.abspath(__file__))
    doc1 = os.path.join(out_dir, "Project_Documentation.pdf")
    doc2 = os.path.join(out_dir, "Daily_Project_Work_Log.pdf")
    print(f"Generating black-and-white {doc1}...")
    generate_project_documentation(doc1)
    print(f"Generating black-and-white {doc2}...")
    generate_daily_work_log(doc2)
    print("Generation complete.")
