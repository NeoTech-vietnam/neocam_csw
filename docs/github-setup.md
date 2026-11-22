# GitHub CI setup

The twelve source modules are private repositories in `NeoTech-vietnam`, selected
by Conan-style Git tags in packages.yml. Product configuration and local build
commands belong to `neocam_csw`. Versioned reusable orchestration belongs to
`ci-workflows`. Both repositories are private.

- Product: https://github.com/NeoTech-vietnam/neocam_csw
- Shared CI: https://github.com/NeoTech-vietnam/ci-workflows
- Product workflow: `.github/workflows/integration.yml`
- Shared workflow: `.github/workflows/esp-idf.yml@v1.0.0`

The caller handles push/main, pull requests and workflow_dispatch. Manual inputs
`package` and `package_ref` override one module for that run; they do not change
the committed integration baseline. The reusable workflow uses Ubuntu 24.04,
Python 3.12 and the official `espressif/idf:v6.0.1` Docker image for ESP32-S3.
No physical runner registration or board is needed for compilation.

## Required read-only module credential

GitHub's automatic GITHUB_TOKEN is limited to the caller repository. Reading the
twelve private source repositories requires a separate credential.

1. Create a fine-grained personal access token in your GitHub account settings.
2. Set resource owner to **NeoTech-vietnam**. Choose **Only select repositories**
   and select these twelve source repositories:
   BootCtrl, BswLib, CUCEL, CamApp, CamIo, CamPipe, EbOs, HttpSrv, LocalTime,
   NeoContracts, Rte and WifiStack.
3. Grant repository permission **Contents: Read-only**. Metadata read access is
   included automatically. No write, workflow or organization permissions are
   needed. Choose an expiry appropriate for the team and renew before it expires.
4. In neocam_csw, open Settings → Secrets and variables → Actions and create a
   **repository secret** named **PACKAGE_READ_TOKEN** containing the token.
   Direct link: https://github.com/NeoTech-vietnam/neocam_csw/settings/secrets/actions
5. Keep the token out of chat, source files, Git URLs and committed configuration.
   The caller passes the secret explicitly; it is not stored in ci-workflows.

Alternatively, set the secret from your own terminal using the hidden prompt:

```powershell
gh secret set PACKAGE_READ_TOKEN --repo NeoTech-vietnam/neocam_csw
```

GitHub Free private repositories do not receive organization-level secrets, so
use a repository secret for this setup. A read-only GitHub App installation token
can replace the personal token later without changing the package model.

## Run and inspect the product build

Open neocam_csw → Actions → NeoCam integration → Run workflow. Leave both inputs
empty for the committed baseline. For a module experiment, supply e.g. `WifiStack`
and a pushed branch/tag/SHA. Download the artifact for firmware binaries, ELF/map,
flash arguments, resolved module commit SHAs and validation logs.

A missing credential fails early with an explicit message, before downloading
private modules. Infrastructure smoke results in ci-workflows compile the SDK's
stock hello_world example; they do not count as a NeoCam product validation.

## Shared workflow access and releases

ci-workflows → Settings → Actions → General → Access must permit callers from
NeoTech-vietnam. This private-workflow download permission is separate from the
module credential above. Select a published CI tag in the project caller and keep
published tags unchanged; future updates get a new version and an explicit caller
upgrade. Shared workflow checkout uses the calling project, not the CI repository.

## Later: automatic integration tests from a module repository

After module CI succeeds, its workflow can call the integration workflow-dispatch
API using a credential with Actions: write on neocam_csw. Pass the module's tested
full commit SHA as package_ref and its manifest key as package. This runs a test;
it does not promote the module into the committed baseline. Automatic cross-repo
triggers and physical flashing are separate future setup steps.

References:
- https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows
- https://docs.github.com/en/actions/how-tos/reuse-automations/share-with-your-organization
- https://docs.github.com/en/actions/concepts/security/github_token
- https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets
