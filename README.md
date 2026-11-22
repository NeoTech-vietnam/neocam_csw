# NeoCam integration workspace

This repository selects module versions and owns NeoCam product configuration.
Fetched source appears at the root, like the MMD project. Each source module is
maintained in its own repository outside this project. Nothing here requires a
Conan server. `packages.yml` is a Git workspace manifest, not a Conan recipe.

## Fetch and build

Use Python 3.12 or newer, Git, and a C compiler (`cc`, or set `CC`).
On Windows the host runner puts the chosen compiler's DLL directory first for its
own process; this avoids conflicts between multiple installed MinGW toolchains.

```powershell
python -m pip install -r TOOLCONF/requirements-dev.txt
python TOOLCONF/workspace.py fetch
python TOOLCONF/workspace.py status
python test/run_host_tests.py
```

The manifest selects private repositories in the
[NeoTech-vietnam organization](https://github.com/NeoTech-vietnam), using tags such
as `bootctrl/1.0.0@neotech/prototype`. Authenticate Git with an account that can
read those repositories. Run these commands from this directory. A fetch exports
committed files, including module-owned source lists and tests, without embedding
Git histories here. The original local bootstrap selections remain in Git history.

Published tags are stable version selections: keep them unchanged, and create a
new version for changed code. Exact resolved commit SHAs are recorded under `_out`.

If a fetch fails specifically with `Could not resolve proxy`, the tool retries
that fetch once using `git -c http.proxy=` and prints a notice. This bypasses the
configured Git proxy for that command only; no saved Git settings are changed.
Other errors, including authentication failures and missing refs, are not retried.

In an exported **ESP-IDF 6.0.1** terminal:

```powershell
idf.py -B _build/esp32s3 build
python TOOLCONF/check_build.py _build/esp32s3
idf.py -B _build/esp32s3 -p COM3 flash monitor
```

Set the real serial port yourself. The SDK, camera 2.1.7 and JPEG 1.3.1 pins are
retained. Wi-Fi, HTTP, preview/photo behavior and the existing public C APIs are
preserved. See [runtime.md](docs/runtime.md) for endpoints and board details.

## Ownership

| Location | Owner and purpose |
| --- | --- |
| `Conf/<module>` | Product values, tuning macros and memory-section configuration |
| `Conf/__CONFIG` | Startup composition and ESP-IDF entry point |
| `GConf/CameraProfiles` | Product-wide camera profile values |
| `TOOLCONF` | Fetching, IDF build wrappers, performance tools and checks |
| `packages.yml` | Authoritative module repository/ref/destination selection |
| Root module directories | Fetched snapshots or explicit development links; ignored by integration Git |
| `test` | Cross-module regressions and the common host-test runner |
| `.workspace`, `_out`, `_build` | Generated cache/state, reports and build output |

Each module owns `module.cmake`, implementation, API/configuration types and its
module tests. The integration build preserves the logical BSW/Rte/ApplicationLayer
IDF groups. These compilation groups do not dictate repository boundaries.
`CamApp` is a NeoCam-specific package with ASW/ASV/DE subdirectories.
`NeoContracts` owns shared types without extending standard Platform_Types.h.
The current CamPipe backend reads Wi-Fi configuration for diagnostics; this
existing dependency is explicit in the shared BSW build, not removed in this migration.

## Develop Wi-Fi outside the project

Create a branch in `../modules/WifiStack` using Git. Copy
`packages.local.example.yml` to the ignored `packages.local.yml`, then:

```powershell
python TOOLCONF/workspace.py fetch --overrides packages.local.yml
python test/run_host_tests.py --case wifi_manager
```

`WifiStack` is now a junction on Windows or a symlink on Linux. Both uncommitted
edits and branch switches in the external checkout are immediately visible to
builds. Tests still use this project's configuration and dependency selection.
Run `python TOOLCONF/workspace.py fetch` without `--overrides` to restore the
pinned snapshot; the external checkout and its edits are preserved.

For a committed branch experiment without a live link:

```powershell
python TOOLCONF/workspace.py fetch --ref WifiStack=feature/my-wifi-change
```

That changes the current assembly only. To promote the result, replace `ref` in
`packages.yml` with the tested full commit SHA and commit the manifest. Fetch
records resolved SHAs in `_out/packages-resolved.json`. `status` reports local
dirty checkouts and changed selections. Treat snapshots as disposable consumed
content, but preserve edits before fetching: replacement of modified snapshots
or unmanaged folders is refused. No automatic reset, clean or stashing occurs.
When adding a new package destination, add a root ignore entry such as `/NewModule`
without a trailing slash, so both snapshot directories and live links are ignored.

## Publish and activate GitHub

See [GitHub setup](docs/github-setup.md). The container directory and `modules`
directory are not repositories. All twelve module repositories are now published
privately, with `origin` set in their independent local checkouts. Their existing
histories were preserved. This project is published as
[`NeoTech-vietnam/neocam_csw`](https://github.com/NeoTech-vietnam/neocam_csw).

The small `.github/workflows/integration.yml` caller handles pushes to main, pull
requests and manual dispatch. It uses the versioned ESP-IDF workflow in
[`NeoTech-vietnam/ci-workflows`](https://github.com/NeoTech-vietnam/ci-workflows).
Configure repository secret `PACKAGE_READ_TOKEN` with Contents: read access to
the twelve private modules. Build results and artifacts belong to this project.
Build scripts and product configuration remain here; shared CI owns orchestration.

For manual flashing of a successful main integration artifact, follow the
[Ubuntu self-hosted runner setup](docs/self-hosted-flashing.md). **NeoCam flash**
uses the shared `flash-esp32.yml@v1.2.0` workflow and a dedicated USB board runner;
compilation continues on GitHub-hosted Ubuntu. No additional package-read token
is needed for artifact download. After flashing, IDF Monitor captures 30 seconds
of serial output by default and uploads `serial-monitor.log`. The dispatch form
lets you change the duration and console baud rate, or set duration `0` to skip.

WifiStack development pushes can also trigger a reference build on
`feat/wifistack`, selected in its module-owned `ci_targets.yml`. See
[module integration setup](docs/module-integration.md). The dedicated receiver
tests the exact pushed module SHA and rejects main/default branch targets.

## Provenance and validation

`_metadata/source-mapping.json` records the original NeoLab commit, source hashes
and ownership mapping. [migration.md](docs/migration.md) explains the differences
from EA211. [_metadata/validation.json](_metadata/validation.json) records the
original migration validation. Current hosted CI runs and their artifacts provide
the evidence for the published integration baseline; physical board checks remain
separate from compilation and host regressions.
