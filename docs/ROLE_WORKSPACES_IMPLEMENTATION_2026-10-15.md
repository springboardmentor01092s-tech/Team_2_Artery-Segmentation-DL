# Role workspaces — implementation status

The supplied “CoroVision AI — User Roles, RBAC and Dashboard Structure” is the
target policy. Its embedded Mermaid CSS is formatting, not executable project
instructions. The actual app is React/TypeScript + FastAPI + SQLAlchemy; it is
not Express/Firebase/Firestore. No authentication-provider migration was made.

## Implemented

- Shared shell, role-specific navigation labels, medical/research SVG icons and
  capability cards. Cards link to existing shared tools, rather than pretending
  every engine has an independent implementation.
- Standard User maps to the existing `viewer` database role. Password and Google
  registrations now start read-only. Existing users are not silently downgraded.
- Standard/viewer workspace remains focused on assigned case details, recorded
  clinical findings, report status and assigned clinicians, per the user's earlier
  requirement. It does not show model evaluation or engineering controls.
- Researcher and clinician workspaces have labelled engine/review entry points.
  Model validation is no longer displayed on the clinician dashboard.
- ML overview focuses on the model lifecycle, without patient-case access.
- Administrator overview focuses on governance, not a medical-case inventory.
- Access requests in Settings; administrator approval/rejection queue. Requests
  grant no privileges. Decisions require notes and are audited; self-approval and
  repeated decisions are denied. Professional/institutional eligibility must be
  checked manually outside the app; no automated credential verification exists.
- Administrator role alone no longer grants case listing, image access or export.
  Case ownership/explicit assignment is enforced by the existing server policy.
  Trash restore returns only operational metadata, not medical case contents.
- Model activation is administrator-only and audited; researcher and ML registry
  views are read-only. Activation is a research-checkpoint switch, not clinical
  deployment authorization.
- Non-active accounts are denied by authentication middleware. Backend role checks
  use current database state, not browser-supplied role strings.
- Doctor/clinician aliases and the technician intake role remain compatible.
- Settings appearance controls remain at the bottom. Header theme previews and
  dashboard notification duplicates remain removed. Training remains paused.

## Not complete / not claimed

- Dataset library/registry, dataset-specific grants and licence enforcement,
  retention policies and versioned research projects are not integrated services.
- Live training controls, compute/GPU monitoring, experiment submission and
  explanation-fidelity tests are not connected. No training is started.
- Deployment-candidate submission and a multi-stage production approval gate are
  not implemented. No production or clinical deployment claim is made.
- Standard-user synthetic demo analysis is not implemented; only authorized,
  read-only results are exposed to that role.
- Automated severity grading is not validated. Severity is clinician-entered.
- Institutional SSO needs a real identity provider. Firebase token verification
  and Firestore rules do not apply to the current stack and were not added.
- Detailed staff contact directories and credential verification need an approved
  institutional source. Only actual assigned clinician names/roles are shown.

## Verification

Frontend TypeScript/Vite production build passed. 41 selected API/authentication,
RBAC, access-request, shared workflow, model-registry, image and volume tests
passed. Legacy image-workflow tests now explicitly provision researcher fixtures;
they no longer assume registration grants elevated access. Tests use an isolated
temporary database and storage.

The build still reports its existing bundle-size advisory. Test JWT keys generate
a short-test-key warning; test credentials are not production configuration.
Browser visual verification was blocked by the locked Mac. Mobile, screen-reader
and full production-security audits have not been completed.
