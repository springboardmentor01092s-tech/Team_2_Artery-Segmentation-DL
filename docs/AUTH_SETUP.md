# CoroVision AI authentication setup

The app supports password sign-in with a unique username or email address.
Registration requires an email. Phone authentication is outside this project scope.

Google and GitHub sign-in use server-side OAuth authorization code flows. Create
OAuth clients yourself and set their IDs and secrets as backend environment
variables; never put a client secret in the frontend. A verified provider email
creates a researcher account. A social account is not automatically linked to
an existing password account with the same email. To link it, sign in with the
existing account and use **Profile and security → Connected accounts**.

## Local OAuth configuration

Set `FRONTEND_ORIGIN` and `OAUTH_REDIRECT_BASE` to the same browser origin,
usually `http://127.0.0.1:5173`. Register these exact callback URLs:

- Google: `http://127.0.0.1:5173/api/auth/oauth/google/callback`
- GitHub: `http://127.0.0.1:5173/api/auth/oauth/github/callback`

Copy `backend/.env.example` to `backend/.env` and fill in the relevant values.
The backend loads this file when it starts, and `.gitignore` excludes it. Restart
the backend after editing the file. Do not paste client secrets into the chat,
frontend source, or Git. The buttons enable only when both credentials for a
provider are set.

Create a [Google OAuth web client](https://developers.google.com/identity/protocols/oauth2/web-server#creatingcred)
and a [GitHub OAuth app](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/creating-an-oauth-app).
Set `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GITHUB_CLIENT_ID`, and
`GITHUB_CLIENT_SECRET` in `backend/.env`. Google uses `openid email profile`
scope. The GitHub OAuth app requests `user:email`.
The Vite development server proxies `/api` to the backend. For deployment, use
HTTPS and route `/api` to FastAPI.

The backend checks the OAuth `state` cookie, uses provider account IDs, requires
a verified email, and sends the browser a short-lived one-time ticket. The
frontend exchanges that ticket for its normal revocable app session; provider
tokens are not stored in the browser or database.

## Password reset delivery

Set `SMTP_HOST`, `SMTP_PORT`, `SMTP_FROM`, and, if required, `SMTP_USERNAME` and
`SMTP_PASSWORD` to enable email codes. Port 587 uses STARTTLS; port 465 uses
implicit TLS. Example variable names are in `backend/.env.example`.

Reset codes have six digits, expire after ten minutes, allow at most five
attempts, and have per-account resend limits. A successful reset revokes all
existing sessions. The API does not return reset codes.

If email delivery is not configured, password recovery is unavailable;
the app does not pretend to send a message. Keep credentials in the environment
or a secret manager. Use a dedicated test account and provider sandbox to verify
delivery and redirects before exposing the app beyond local development.
# Local prototype sign-in convenience

In the local prototype, **Keep me signed in on this device** is selected by default. When `CV_LOCAL_DEMO_SESSIONS=1` is set in the local backend `.env`, a remembered password login or social login lasts 30 days. Without that setting, sessions last eight hours. Sign out, password changes, account suspension, and session expiry still invalidate access.

On `localhost` and `127.0.0.1`, each account signed in with the remembered option is added to a browser-local account switcher. You can switch from the profile menu without entering its password again while its own session remains valid. Accounts must sign in once first. The switcher is hidden on other hosts and never stores passwords. Remove `CV_LOCAL_DEMO_SESSIONS=1` before deployment and avoid using the local account switcher on a shared browser.

The local demo setup creates accounts for `admin`, `doctor`, `clinician`, `researcher`, `ml_engineer`, `technician`, and `viewer`. Run `python3 seed_demo_accounts.py` from `backend` to add missing accounts without replacing existing passwords. Usernames and generated passwords are in the Git-ignored, owner-readable `backend/demo-credentials.json`. Sign in to each account once in the same browser to make all seven appear in the switcher.
