# Initial administrator access

CoroVision AI has no default administrator password. Each installation creates its own first administrator in a private server terminal.

## First deployment

Run the interactive command inside the deployed application container:

```bash
python -m app.cli create-admin
```

With Docker Compose:

```bash
docker compose exec app python -m app.cli create-admin
```

With a Railway shell:

```bash
railway ssh -- python -m app.cli create-admin
```

The command prompts for an email and password without accepting the password in command-line arguments or environment variables. Passwords require 14–128 characters with uppercase, lowercase, number and symbol characters. The command refuses to run after an administrator exists. Production registration requires a valid invitation and creates a viewer account.

Additional roles are assigned through the authenticated Administrator workspace and are audited. There is no shared credential between installations.

## Server-owner recovery

An authenticated deployment owner with private container access can run:

```bash
python -m app.cli reset-admin-password
```

The command prompts securely, only resets an existing administrator, revokes that administrator’s sessions, clears the current authenticator and login throttle, and writes an audit event. The administrator enrolls a new authenticator at the next production sign-in. It is not exposed as a public API.

## First sign-in and invitations

1. Open the installation URL and sign in with the bootstrapped credentials.
2. Add the displayed setup key to a time-based authenticator and enter its six-digit code. Subsequent production sign-ins require the password and a fresh authenticator code.
3. In **User Management**, enter the recipient’s email and create an invitation. Share the link privately. It expires in 24 hours and can be redeemed once using that email.
4. Use the existing role and case-access controls to assign any additional permissions after registration.

The browser keeps the login session in tab storage. Production administrators must complete MFA before accessing protected routes. Production OAuth cannot create a new account. Deployment owners should restrict access to the database and its backups because they contain authenticator secrets. Use HTTPS for hosted sign-in.
