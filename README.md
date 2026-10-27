# prisma-airs-claude-code-cli-okta-auth

This repository gives you an Okta sign-in for the Claude Code CLI. Claude Code
sends each request to a Prisma AIRS AI Gateway (AIGW) deployment. Okta issues
a JWT. The gateway checks the JWT on each request.

Use this guide to set up Okta, then connect Claude Code to it on macOS or
Windows.

## What you need

- An Okta tenant with admin access.
- Python 3 (stock, no extra packages) on the machine that runs Claude Code.
- `bash` and `curl` and `openssl`, only if you want the bash helper script on
  macOS or Linux.
- Access to the gateway's expected audience and issuer values.

## Step 1: Create the Okta app

1. In the Okta Admin Console, go to **Applications → Create App Integration**.
2. Pick **OIDC - OpenID Connect**, then pick **Native Application**.
3. On the **General** tab, under **Grant type**, check **Authorization
   Code** and **Refresh Token**.
4. Make sure **Proof Key for Code Exchange (PKCE)** stays checked. Okta
   checks this box by default for Native apps.
5. Under **Client Credentials**, set **Client authentication** to **None**
   (public client / PKCE). Do not use **Client secret** for this app.
6. Add a **Sign-in redirect URI**: `http://localhost:8080/callback`. Use a
   different port if you plan to set `OKTA_REDIRECT_PORT` to a different
   value.
7. Save the app, then open its **Assignments** tab and assign your test
   user or group.
8. Copy the app's **Client ID**. You need it in Step 3.

## Step 2: Confirm the authorization server and scopes

1. Go to **Security → API → Authorization Servers**.
2. Pick the authorization server the gateway trusts (often `default`, or a
   custom one your gateway team set up).
3. Note the server's **ID** and **Audience** value.
4. On the **Scopes** tab, make sure `openid`, `profile`, `email`, and
   `offline_access` exist. Okta's `default` server has these scopes
   already.
5. On the **Access Policies** tab, add or edit a rule for this app. Set the
   grant type condition to **Authorization Code**. Set the scope list to
   `openid profile email offline_access`.

If your gateway needs a custom claim (for example, a workspace ID or a
config slug), add it on the **Claims** tab. Use an expression keyed on
`app.clientId` if different apps need different claim values.

## Step 3: Set your local configuration

1. Copy `.env.template` to `.env`.
2. Fill in your real values:

```bash
OKTA_DOMAIN=https://your-org.okta.com
OKTA_CLIENT_ID=<the Client ID from Step 1>
OKTA_REDIRECT_PORT=8080
OKTA_AUDIENCE=<the Audience value from Step 2>
OKTA_AUTH_SERVER=<the authorization server ID from Step 2>
```

1. Do not commit `.env`. The `.gitignore` file already excludes it.
2. If a TLS-inspecting proxy sits between you and Okta, set
   `OKTA_CA_BUNDLE` to the path of a CA bundle file in PEM format. Leave it
   blank for a normal network.

## Step 4: Test the helper script by hand

Run this test before you wire the script into Claude Code. It confirms
Okta issues a token and the script caches it.

```bash
set -a; source .env; set +a
python3 okta-token-helper.py
```

A browser window opens for Okta sign-in. After you sign in, the script
prints an access token to standard output. Run the command again. The
second run returns the cached token at once, with no browser step.

## Step 5: Install the script and connect it to Claude Code

Copy the helper script to `~/.claude/`, not the git checkout folder. This
path stays stable no matter where you cloned this repository, and it
matches where Claude Code already keeps `okta-cache/`.

```bash
cp okta-token-helper.py ~/.claude/okta-token-helper.py
```

Claude Code calls your configured `apiKeyHelper` command on each request.
It sends that command's standard output as the `Authorization: Bearer` and
`X-Api-Key` header values. **Claude Code runs this command in an isolated
environment.** Your shell's `.env` file is not available to it. List every
Okta variable directly in the `env` block of your Claude Code settings
file.

Edit `~/.claude/settings.json` (user-level) or `.claude/settings.json`
(project-level):

### macOS

```json
{
  "apiKeyHelper": "python3 ~/.claude/okta-token-helper.py",
  "env": {
    "ANTHROPIC_BASE_URL": "https://your-gateway-host",
    "OKTA_DOMAIN": "https://your-org.okta.com",
    "OKTA_CLIENT_ID": "0oa1b2c3d4YourClientId",
    "OKTA_AUDIENCE": "api://default",
    "OKTA_AUTH_SERVER": "default",
    "OKTA_REDIRECT_PORT": "8080"
  }
}
```

You can also copy `okta-token-helper.sh` to `~/.claude/` instead, and set
`apiKeyHelper` to `bash ~/.claude/okta-token-helper.sh`.

### Windows

Windows has no bash by default, so use the Python script. Copy it to
`%USERPROFILE%\.claude\okta-token-helper.py`. Claude Code does not expand
`~` in the `apiKeyHelper` field on Windows ([known
issue](https://github.com/anthropics/claude-code/issues/13013)). Use the
full path instead.

```json
{
  "apiKeyHelper": "python C:\\Users\\you\\.claude\\okta-token-helper.py",
  "env": {
    "ANTHROPIC_BASE_URL": "https://your-gateway-host",
    "OKTA_DOMAIN": "https://your-org.okta.com",
    "OKTA_CLIENT_ID": "0oa1b2c3d4YourClientId",
    "OKTA_AUDIENCE": "api://default",
    "OKTA_AUTH_SERVER": "default",
    "OKTA_REDIRECT_PORT": "8080"
  }
}
```

Replace `you` with your real Windows username. Make sure `python` is on
your Windows `PATH`. Test this with `python --version` in a new terminal
window before you edit the settings file.

For both platforms, add `OKTA_CA_BUNDLE` to the `env` block too, if you
set it in Step 3.

## Step 6: Run Claude Code

Start Claude Code and send any prompt. The first run opens a browser for
Okta sign-in. Later runs reuse the cached token and skip the browser step.

## How token refresh works

Claude Code calls your `apiKeyHelper` command again every 5 minutes by
default, and right after any HTTP 401 response from the gateway. The
helper script also tracks the token's own expiry. It silently exchanges
the refresh token for a new access token once the cached one comes within
60 seconds of expiry.

If your authorization server issues short-lived access tokens (for
example, a 2-minute TTL), set `CLAUDE_CODE_API_KEY_HELPER_TTL_MS` in the
`env` block to a value in milliseconds under that TTL. This makes Claude
Code call the helper script more often, so the refresh happens in time.

## Troubleshooting

- **404 on the Okta sign-in page:** check `OKTA_DOMAIN` for a typo, and
  check that `OKTA_REDIRECT_PORT` matches a redirect URI registered on the
  app.
- **401 `invalid_client` during token exchange:** check that **Client
  authentication** on the Okta app is set to **None**, not **Client
  secret**.
- **`CERTIFICATE_VERIFY_FAILED`:** set `OKTA_CA_BUNDLE` to a CA bundle that
  covers Okta's real certificate chain. Confirm with `openssl s_client`
  which certificate your network path actually presents before you assume
  a proxy intercepts the connection.

## Project conventions

See [CLAUDE.md](CLAUDE.md) for the full decisions log, the auth flow
design, and the rules this repository follows.
