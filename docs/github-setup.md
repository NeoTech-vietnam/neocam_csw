# Publish independent repositories and enable integration builds

There are thirteen project repositories: twelve children of `modules`, plus
`neocam_csw`. `NeoCamWorkspace` itself is a container directory. Local Git identity
was copied from the existing NeoLab configuration; machine-wide settings were
not changed. Each module has its own `main` branch and initial commit.

1. Create a private GitHub repository for each module and for `neocam_csw`.
   Create empty repositories: do not initialize them with a separate README/history.
2. In each module repository, add its GitHub remote and push the existing `main`
   branch. This preserves the commit SHAs selected in the integration manifest.
3. Replace all `repo: ../modules/NAME` values in the integration `packages.yml`
   with `repo: https://github.com/YOUR_OWNER/NAME.git`. Keep the pinned SHAs.
4. Commit the updated manifest, add the integration remote, and push its `main`.
5. Add an Actions secret named `PACKAGE_READ_TOKEN` to the integration repository.
   Use a fine-grained token with **Contents: read** on the twelve private module
   repositories. Follow any organization approval or SSO requirements. Keep tokens
   out of YAML, URLs and committed Git configuration. A GitHub App installation
   token can replace this setup later.
6. Enable Actions, then select **NeoCam integration → Run workflow**. Leave both
   inputs empty for the baseline, or supply `WifiStack` and a pushed branch/tag/SHA.

The runner is GitHub-hosted Ubuntu. Firmware compilation runs in the official
`espressif/idf:v6.0.1` Docker image, while native host tests run on the runner.
No physical board is required. This migration does not configure a runner, create
GitHub repositories, generate credentials, or run Actions remotely.

The fetcher rejects local bootstrap repository paths and live local overrides in
CI. The workflow uses a temporary Git HTTP authorization header for module reads;
it does not write credentials into repository configuration or artifacts.

## Later: automatic testing from a module repository

After a module CI run succeeds, that workflow can call the integration repository's
workflow-dispatch API using a token authorized for **Actions: write** on the
integration repository. Pass `package: WifiStack` and `package_ref` set to the
module's tested full commit SHA. The integration workflow must already exist on
the default branch; choose the integration branch/tag with the dispatch `ref`.

This starts an integration test; it does not update the committed baseline.
Promote successful module commits through an integration-manifest change/PR.
Automatic cross-repository dispatch is documented, not enabled in this version.

References: [workflow dispatch](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#workflow_dispatch),
[dispatch API](https://docs.github.com/en/rest/actions/workflows#create-a-workflow-dispatch-event),
[GITHUB_TOKEN repository scope](https://docs.github.com/en/actions/concepts/security/github_token).
