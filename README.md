# NeoCam integration workspace

This repository selects module versions and owns NeoCam product configuration.
Fetched source appears at the root, like the MMD project. Each source module is
maintained in its own repository outside this project. Nothing here requires a
Conan server. `packages.yml` is a Git workspace manifest, not a Conan recipe.

## Quick start

Start with **Git**, **Python 3.12+**, and Git authentication for this private
repository and its twelve source modules. Run the commands from `neocam_csw`.
ESP-IDF does not need to be installed beforehand.

### Ubuntu

Ubuntu 24.04 is validated. On Ubuntu 22.04, install Python 3.12+ first; see the
[local development guide](docs/local-development.md) for interpreter selection.

```bash
git clone https://github.com/NeoTech-vietnam/neocam_csw.git
cd neocam_csw
make setup
make build
```

If Make is missing, use `sh neo setup` instead of `make setup` the first time.
Setup installs missing Ubuntu build packages through apt, so sudo may request
your password. It then prepares Python dependencies, fetches modules and installs
the pinned SDK/compiler tools. The initial download can take several minutes;
later builds reuse the installation and do not use sudo.

### Windows PowerShell

Install Git and Python 3.12+ on PATH, then:

```powershell
git clone https://github.com/NeoTech-vietnam/neocam_csw.git
cd neocam_csw
.\neo.cmd setup
.\neo.cmd build
```

GNU Make is optional on Windows. The launcher reuses a matching SDK installation
or downloads the required version. Host tests additionally need MinGW-w64 `cc`
on PATH, or a compatible native C compiler selected through `CC`.

Both interfaces select **ESP-IDF 6.0.1**, **ESP32-S3** and `_build/esp32s3`
automatically. Builds activate the SDK and check the generated firmware. Camera
2.1.7 and JPEG 1.3.1 remain pinned. Firmware is written to
`_build/esp32s3/neocam_csw.bin`. No manual SDK activation is needed.

New SDK installations use the shared, versioned `~/.neotech/toolchains` cache.
Existing `.neocam` or workspace SDK installations remain reusable. Each project
keeps its own Python tools in `.workspace/dev-venv` and its own build output.

## Daily commands

After editing source or configuration, repeat **`make build`** on Ubuntu or
**`.\neo.cmd build`** on Windows. Use `check` when you also want host regressions.

| Ubuntu / Make | Windows PowerShell | Purpose |
| --- | --- | --- |
| `make setup` | `.\neo.cmd setup` | One-time dependencies, packages and SDK setup |
| `make build` | `.\neo.cmd build` | Compile and verify firmware |
| `make test` | `.\neo.cmd test` | Run host regressions |
| `make check` | `.\neo.cmd check` | Run tests, build and verify firmware |
| `make dev MODULE=WifiStack` | `.\neo.cmd dev WifiStack` | Connect a live module checkout |
| `make fetch` | `.\neo.cmd fetch` | Refresh selected packages |
| `make baseline` | `.\neo.cmd baseline` | Restore pinned source selection |
| `make status` | `.\neo.cmd status` | Show consumed revisions and live checkouts |
| `make doctor` | `.\neo.cmd doctor` | Show detected SDK and local settings |
| `make ports` | `.\neo.cmd ports` | List serial devices |
| `make flash-monitor` | `.\neo.cmd flash-monitor` | Build, flash and open the serial monitor |

Before flashing, save your actual board port once:

```bash
make port PORT=/dev/serial/by-id/YOUR-DEVICE
```

On Windows, use `.\neo.cmd port COM3`, replacing `COM3` with your board's port.
Ubuntu users need serial-device access, normally through the `dialout` group.
Exit the local monitor with Ctrl+]. Additional commands include `flash`,
`monitor`, `menuconfig`, `clean` and `help`; see
[local development](docs/local-development.md) for details.

## Ownership

| Location | Owner and purpose |
| --- | --- |
| `Conf/<module>` | Product values, tuning macros and memory-section configuration |
| `Conf/__CONFIG` | Startup composition and ESP-IDF entry point |
| `GConf/CameraProfiles` | Product-wide camera profile values |
| `TOOLCONF` | Fetching, IDF build wrappers, performance tools and checks |
| `packages.yml` | Authoritative module repository/ref/destination selection |
| `packages.local.yml` | Ignored live module overrides, managed by the `dev` command |
| `Makefile`, `neo`, `neo.cmd` | Short interfaces to the same local development helper |
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

Select the module once:

```bash
make dev MODULE=WifiStack
```

Or use `.\neo.cmd dev WifiStack` on Windows. This creates an independent checkout
at `../modules/WifiStack` if missing, adds the local override, and connects it to
the project using a symlink on Ubuntu or junction on Windows. Existing branches
and uncommitted edits are preserved. A new clone starts on its default branch.

Use normal Git commands in the module checkout to select your development branch.
For the WifiStack pilot, from neocam_csw:

```bash
git -C ../modules/WifiStack switch feat/wifistack
```

Edit that external checkout and run `make build` or `make check` in neocam_csw.
Both uncommitted edits and branch switches are immediately visible. Repeated
builds do not refetch unchanged source selections. `make baseline` restores pinned
snapshots while keeping the override file and external checkout for later use.

The configuration files have separate responsibilities:

| File | Selects |
| --- | --- |
| `neocam_csw/packages.yml` | Module repositories and committed baseline versions |
| `neocam_csw/packages.local.yml` | Local development checkouts used by local builds |
| `WifiStack/ci_targets.yml` | Project development branches to test after module pushes |

For a committed branch experiment without a live link:

```powershell
python TOOLCONF/workspace.py fetch --ref WifiStack=feature/my-wifi-change
```

This lower-level command changes the current assembly only. To promote a tested
revision, update `ref` in `packages.yml` and commit the manifest through review.
Published tags such as `wifistack/1.0.0@neotech/prototype` remain stable; create a
new version for a changed release. Fetch
records resolved SHAs in `_out/packages-resolved.json`. `status` reports local
dirty checkouts and changed selections. Treat snapshots as disposable consumed
content, but preserve edits before fetching: replacement of modified snapshots
or unmanaged folders is refused. No automatic reset, clean or stashing occurs.
When adding a new package destination, add a root ignore entry such as `/NewModule`
without a trailing slash, so both snapshot directories and live links are ignored.

The Git fetch tool retries `Could not resolve proxy` once using command-scoped
`git -c http.proxy=`. Saved Git settings remain unchanged. Authentication errors
and missing revisions still require correcting access or the selected ref.

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

Fresh Ubuntu SDK setup, `make check` and an incremental `make build` passed in
the [Ubuntu developer command validation](https://github.com/NeoTech-vietnam/neocam_csw/actions/runs/45009301980).
Windows launcher, live module selection, tests and firmware builds were also
verified. This validation did not flash hardware. See [runtime.md](docs/runtime.md)
for board behavior and endpoints.

`_metadata/source-mapping.json` records the original NeoLab commit, source hashes
and ownership mapping. [migration.md](docs/migration.md) explains the differences
from EA211. [_metadata/validation.json](_metadata/validation.json) records the
original migration validation. Current hosted CI runs and their artifacts provide
the evidence for the published integration baseline; physical board checks remain
separate from compilation and host regressions.
