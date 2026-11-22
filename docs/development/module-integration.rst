Module pushes trigger reference-project CI
==========================================

WifiStack is the first enabled module configuration. Other modules can adopt the
same small caller and YAML after this pilot is accepted. Reference integration
uses GitHub-hosted Ubuntu; it does not invoke the USB flashing runner.

.. code:: text

   WifiStack: push development commit
     -> read ci_targets.yml
     -> validate every reference project before dispatch
     -> neocam_csw / feat/wifistack / module-integration.yml
     -> fetch WifiStack at that exact commit, other modules at their normal pins
     -> host regressions + ESP-IDF build + firmware checks
     -> module check reports success/failure and links the project run

Configuration and ownership
---------------------------

WifiStack owns ``ci_targets.yml``:

.. code:: yaml

   ref_projects:
     - repository: NeoTech-vietnam/neocam_csw
       branch: feat/wifistack
       package: WifiStack

This file selects **where to test the module**. The integration project's
``packages.yml`` selects **which module versions compose its baseline**. A CI run
replaces only WifiStack's selected version with the full pushed commit SHA using
``workspace.py fetch --ref WifiStack=<SHA>``; neither manifest nor release tags are
rewritten. No prototype tag is required for every development push.

The module's ``.github/workflows/integration.yml`` triggers on pushes to branches
other than ``main``/``master``, or a manual dispatch on a development branch. It calls
``ci-workflows/.github/workflows/module-integration.yml@v1.3.1``. The shared action
validates targets, dispatches the fixed ``module-integration.yml`` receiver, then
waits for the actual results. Sending the request alone is not a passing check.

The receiver calls ``esp-idf.yml@v1.3.1`` in module mode. Normal baseline integration
and the separate manual flash/monitor workflows keep their existing selections.
Feature artifacts are not eligible for the main-only flash workflow.

Restrictions
------------

- Target branches must exist and begin with ``feat/``, ``feature/``, ``fix/`` or ``dev/``.
- ``main``, the integration project's default branch, tags and SHA targets are
  forbidden, including ref aliases. Sender and receiver both check this.
- Source module revisions must be full commit SHAs. The known package's GitHub
  repository in ``packages.yml`` must match the source repository.
- The YAML supports up to eight distinct reference projects. All are checked
  before any dispatch; builds are started before their results are followed.
- Newer module pushes cancel older waiting module runs. New project runs cancel
  older module integrations for the same project branch/package. Cancellation
  does not cancel unrelated packages or normal baseline builds.

These are rules for this automation. An Actions-write credential is scoped to
repositories, not individual workflow branches; it does not stop an administrator
from manually using another entry point or changing the policy. Keep the dispatch
credential restricted to the selected integration repositories and use normal
review controls for workflow changes.

One-time credential setup for WifiStack
---------------------------------------

The module's automatic ``GITHUB_TOKEN`` can read its own repository, but cannot
dispatch into another repository. Do not reuse the package-read token,
and do not upload your broad desktop GitHub CLI credential.

1. Open `GitHub fine-grained tokens <https://github.com/settings/personal-access-tokens/new>`__.
2. Name it ``NeoCam module integration``; choose an expiry and resource owner
   **NeoTech-vietnam**.
3. Choose **Only select repositories** and select **neocam_csw**.
4. Set repository permissions **Actions: Read and write** and **Contents:
   Read-only**. Metadata read access is automatic. Obtain organization approval
   if GitHub requests it.
5. Generate the token and copy it locally. Do not paste it into chat or YAML.
6. Open `WifiStack Actions secrets <https://github.com/NeoTech-vietnam/WifiStack/settings/secrets/actions>`__.
   Create a **New repository secret** named **INTEGRATION_DISPATCH_TOKEN** with
   that token. This credential belongs under **Secrets**, not Variables.

Alternatively, set it from your authenticated terminal using the hidden prompt:

.. code:: bash

   gh secret set INTEGRATION_DISPATCH_TOKEN --repo NeoTech-vietnam/WifiStack

No additional token is needed in neocam_csw: it continues using its existing
``PACKAGE_READ_TOKEN`` to fetch the module repositories. A missing dispatch secret
fails the module job with setup instructions. After saving it, rerun the failed
WifiStack job or manually run its workflow on ``feat/wifistack``.

For a larger deployment, a GitHub App can supply short-lived installation tokens
instead of a personal token. Repository secrets are the initial setup;
organization-level secret availability depends on the GitHub plan.

Develop and inspect
-------------------

The pilot branches are ``WifiStack/feat/wifistack`` and
``neocam_csw/feat/wifistack``. From your local module checkout:

.. code:: bash

   git switch feat/wifistack
   # Edit and commit your module normally.
   git push origin feat/wifistack

The module workflow passes ``github.sha``, even if you push another commit while a
build is starting. The integration run records the target project SHA, requested
module SHA and resolved package SHAs. The module Actions summary links the
reference builds and its artifact contains ``module-integration-results.json``.
Project firmware artifacts include ``module-ci-request.json`` and
``packages-resolved.json``, plus the existing logs and firmware files.

To change the integration target, create/update a project development branch
containing the receiver and its validation tool, then edit ``branch`` in the
module's ``ci_targets.yml``. The receiver workflow must also exist on the project's
default branch so GitHub can register it for dispatch.

After successful development, promote a reviewed module release through a normal
project manifest change and PR. Keep integration feature branches current by
merging reviewed changes from project main; automatic branch synchronization is
not part of this pilot.

Verification
------------

Shared sender tests: ``python -m unittest discover -s test -p 'test_*.py'`` from
ci-workflows. Receiver tests: ``python test/test_module_ci.py`` from neocam_csw;
these are also included in its full host regression runner. Tests cover forbidden
targets, exact SHA selection, repository matching, failed/cancelled builds,
timeouts and partial dispatch reporting. No test flashes hardware.

The architecture follows the reference-project configuration, shared workflow
delegation and consolidated-result ideas reviewed in the local example. No
enterprise workflow implementation or enterprise service dependency is copied.

References:

- `GitHub workflow dispatch API <https://docs.github.com/en/rest/actions/workflows#create-a-workflow-dispatch-event>`__.
- `Workflow dispatch events and branches <https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#workflow_dispatch>`__.
- `Automatic GITHUB_TOKEN scope <https://docs.github.com/en/actions/concepts/security/github_token>`__.
