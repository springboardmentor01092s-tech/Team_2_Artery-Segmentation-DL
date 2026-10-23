# Milestone 1 wireframes

## Login / registration

```text
┌─────────────────────────────────────────────┐
│ CoroVision AI · Group 3                      │
│ Research prototype                          │
│                                             │
│ Email                                       │
│ [_______________________________________]   │
│ Password                                    │
│ [_______________________________________]   │
│ [ Sign in ]    [ Create researcher account ]│
│                                             │
│ Use de-identified images only.              │
└─────────────────────────────────────────────┘
```

## Cases and upload

```text
┌─────────────────────────────────────────────────────────────────────┐
│ CoroVision AI                          account             Sign out │
├─────────────────────────────────────────────────────────────────────┤
│ Cases                                       [ New case ]            │
│ ┌──────────────┬──────────────┬───────────┬──────────────────────┐ │
│ │ Case code    │ Modality     │ Status    │ Created              │ │
│ └──────────────┴──────────────┴───────────┴──────────────────────┘ │
│                                                                     │
│ Selected case                                                       │
│ [ Choose PNG, JPEG or DICOM ] [ Upload ]                            │
│ ┌───────────────────────────┐  Original size / spacing / status    │
│ │ 512×512 processed preview │  Analysis: future milestone          │
│ └───────────────────────────┘                                       │
└─────────────────────────────────────────────────────────────────────┘
```

## Interaction requirements

Visible field labels and inline errors; keyboard focus and 44px controls;
responsive layout; loading feedback during uploads; no diagnosis wording
until a reviewed model is integrated.

## Profile and security

```text
┌─────────────────────────────────────────────────────────────┐
│ Cases   Profile & security   [Administration for admins]    │
├─────────────────────────────┬───────────────────────────────┤
│ Profile                     │ Change password               │
│ Display name / email        │ Current / new password        │
│ [Save profile]              │ [Change password]             │
├─────────────────────────────┼───────────────────────────────┤
│ Sessions                    │ Recent activity               │
│ Current / previous status   │ Login / profile / case events │
│ [Sign out all sessions]     │                               │
└─────────────────────────────┴───────────────────────────────┘
```

The Administration view shows user accounts with role selectors and recent
audit events. Only administrators can access those API endpoints.

## Research analysis extension

The case view now includes a **Run analysis** action for uploaded images, a
color overlay (cyan artery, coral suspected stenosis), model version, mask pixel
counts, validation Dice, and a research-only interpretation note.

The case view also has an editable de-identified context form (pseudonymous
patient code, age band, gender, coded medical history and risks, scan date,
clinical notes), an image selector, optional ROI/DICOM frame upload controls,
preprocessing steps, and an analysis history list. Two historical runs can be
selected for a pixel-count comparison with a non-clinical interpretation note.
