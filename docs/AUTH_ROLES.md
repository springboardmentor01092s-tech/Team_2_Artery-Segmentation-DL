# Authentication and Role-Based Access Control (RBAC)

CoroVision AI implements full Role-Based Access Control (RBAC) to ensure users only view, modify, review, or export authorized clinical and research data.

## 1. Five Core User Roles

| Role | Stored Keys | Key Responsibilities | Access Boundaries |
| :--- | :--- | :--- | :--- |
| **System Administrator** | `admin` | User management, role assignment, account activation/suspension, model status, audit logs | System governance; clinical reviews require a doctor/clinician role |
| **Doctor / Clinical Reviewer** | `doctor`, `clinician` | Review authorized patient cases, inspect angiography and stenosis localization, record clinical review decisions & approvals | Cannot administer system users or change deployed models |
| **Medical Researcher** | `researcher` | Work with accessible de-identified cases, run inference, inspect recorded validation Dice, export authorized case data | Cannot perform clinical reviews or manage users |
| **ML Engineer** | `ml_engineer` | Inspect deployed model status and recorded validation results | Does not receive case access from this role alone |
| **Technician / Data Operator** | `technician` | Create cases, upload authorized medical images (DICOM/raster), verify preprocessing quality and metadata | Cannot sign clinical reviews or administer AI models |
| **Viewer / Student** | `viewer` | Read-only observation of assigned research cases, segmentation overlays, and AI metrics | Cannot upload, edit, analyze, approve, or export restricted data |

---

## 2. Permission Matrix

| Feature / Action | Admin | Doctor | Researcher | Technician | Viewer |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Manage users and assign roles** | Full | — | — | — | — |
| **Activate / Suspend accounts** | Full | — | — | — | — |
| **Create patient cases** | Yes | Yes | Yes | Yes | — |
| **Upload medical images & DICOM** | Yes | Yes | Approved data | Yes | — |
| **View assigned cases** | All | Authorized | De-identified | Assigned | Read-only |
| **Run AI vessel analysis** | Yes | Yes | Yes | Yes | — |
| **View segmentation & stenosis overlays** | Yes | Yes | Yes | Yes | Yes |
| **Record clinical review decisions** | — | **Yes**, with case review access | — | — | — |
| **View recorded model evaluation** | Yes | — | Yes | — | — |
| **Export cases & reports** | Restricted | Authorized | Research data | — | — |
| **View audit logs** | All system logs | Own activity | Own activity | Own activity | Own activity |

---

## 3. Account Lifecycle & Security Enforcement

1. **New Account Registration**: Public signups default to the `researcher` role. Elevated permissions are assigned by an Administrator.
2. **Account Suspension & Deactivation**: Admins can suspend accounts instantly; existing JWT sessions are revoked, and login is blocked with HTTP 403.
3. **Case-Level Access Sharing**: Case owners or admins can assign specific access levels (`read`, `review`, `edit`) to users using the Case Access system.
4. **Clinical Decision Audit**: Doctor approvals and clinical severity assessments are stored with reviewer attribution and audit timestamps.
