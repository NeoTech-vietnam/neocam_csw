Simple local commands on Ubuntu and Windows
===========================================

The root Makefile and the ``neo`` launchers call the same Python helper. It owns the
SDK version, ESP32-S3 target, build directory, environment activation and source
assembly. Normal builds need no ``export.sh``, ``activate.ps1``, build-path flags or
repeated package fetching.

.. _fresh-ubuntu-2404-computer:

Fresh Ubuntu 24.04 computer
---------------------------

Start with Git and Python 3.12+ available (Ubuntu 24.04 supplies Python). If needed:

.. code:: bash

   sudo apt update
   sudo apt install -y git python3 make

Clone the public neocam_csw repository and enter its directory. Then:

.. code:: bash

   make setup
   make build

``setup`` prepares an ignored project Python venv, fetches packages and downloads
ESP-IDF **v6.0.1**, its ESP32-S3 compiler tools and its Python environment. The
first SDK download is large and can take several minutes. It is reused afterward.
No preinstalled ESP-IDF, Docker or Conan server is required.

On Ubuntu, setup detects and installs missing OS build packages through apt;
sudo may ask for your password once. If Make is absent, run ``sh neo setup`` first;
setup installs Make too. Normal builds do not use sudo or apt. Non-Ubuntu Linux
systems need equivalent prerequisites installed using their own package manager.

The project requires Python **3.12 or newer**. Ubuntu 24.04 provides that version.
For Ubuntu 22.04, supply Python 3.12+ first, then select it when necessary, e.g.
``make setup PYTHON=python3.12``. Other Ubuntu releases need the equivalent packages.

Fresh Windows computer
----------------------

Install Git and Python 3.12+ and ensure they are on PATH. From neocam_csw:

.. code:: powershell

   .\neo.cmd setup
   .\neo.cmd build

GNU Make is optional on Windows. ``neo.cmd`` exposes the same commands. If Make is
already installed, ``make setup`` and ``make build`` work too. The helper downloads
the SDK/compiler tools itself and also reuses this workspace's existing
``../.toolchain`` installation when its SDK tag is v6.0.1. Use a workspace/cache path
without spaces on Windows, following ESP-IDF's path requirements.

Host regression tests additionally need a native C compiler: ``build-essential``
on Ubuntu, or MinGW-w64 ``cc`` on Windows. ``CC`` can select another compatible native
compiler. Firmware compilation uses the downloaded ESP32-S3 compiler and does not
require a separate native C compiler on Windows.

Develop a module
----------------

One-time selection on Ubuntu:

.. code:: bash

   make dev MODULE=WifiStack

On Windows:

.. code:: powershell

   .\neo.cmd dev WifiStack

This clones the independent repository into ``../modules/WifiStack`` if missing,
adds it to ignored ``packages.local.yml``, and assembles its live symlink (Ubuntu)
or junction (Windows). Existing checkout branches and uncommitted edits are
preserved. A new clone initially uses the repository's default branch; use normal
Git commands in that checkout to choose/create your development branch, such as
``git switch feat/wifistack`` for our pilot.

After editing module or project files, repeat just:

.. code:: bash

   make build

Or ``make check`` to run all host tests and build. On Windows use ``.\neo.cmd build``
or ``.\neo.cmd check``. Live source edits are visible immediately. The helper
refetches only when source-selection files change or the assembly is missing;
``make fetch`` explicitly refreshes remote branch snapshots when desired.

Commands
--------

+--------------------------------------------------+-----------------------------+----------------------+
| Ubuntu / Make                                    | Windows equivalent          | Behavior             |
+==================================================+=============================+======================+
| ``make setup``                                   | ``.\neo.cmd setup``         | Prepare packages,    |
|                                                  |                             | dependencies and     |
|                                                  |                             | pinned SDK           |
+--------------------------------------------------+-----------------------------+----------------------+
| ``make dev MODULE=WifiStack``                    | ``.\neo.cmd dev WifiStack`` | Use a live           |
|                                                  |                             | independent module   |
|                                                  |                             | checkout             |
+--------------------------------------------------+-----------------------------+----------------------+
| ``make build``                                   | ``.\neo.cmd build``         | Build and verify     |
|                                                  |                             | firmware             |
|                                                  |                             | configuration        |
+--------------------------------------------------+-----------------------------+----------------------+
| ``make test``                                    | ``.\neo.cmd test``          | Run host regressions |
+--------------------------------------------------+-----------------------------+----------------------+
| ``make check``                                   | ``.\neo.cmd check``         | Tests, firmware      |
|                                                  |                             | build and checks     |
+--------------------------------------------------+-----------------------------+----------------------+
| ``make fetch``                                   | ``.\neo.cmd fetch``         | Refresh selected     |
|                                                  |                             | snapshots/live links |
+--------------------------------------------------+-----------------------------+----------------------+
| ``make baseline``                                | ``.\neo.cmd baseline``      | Restore pinned       |
|                                                  |                             | packages; keep saved |
|                                                  |                             | local override       |
|                                                  |                             | configuration        |
+--------------------------------------------------+-----------------------------+----------------------+
| ``make status``                                  | ``.\neo.cmd status``        | Show consumed        |
|                                                  |                             | revisions and local  |
|                                                  |                             | source checkouts     |
+--------------------------------------------------+-----------------------------+----------------------+
| ``make doctor``                                  | ``.\neo.cmd doctor``        | Show detected SDK,   |
|                                                  |                             | compiler and local   |
|                                                  |                             | settings             |
+--------------------------------------------------+-----------------------------+----------------------+
| ``make ports``                                   | ``.\neo.cmd ports``         | List serial devices  |
+--------------------------------------------------+-----------------------------+----------------------+
| ``make port PORT=/dev/serial/by-id/YOUR-DEVICE`` | ``.\neo.cmd port COM3``     | Remember the         |
|                                                  |                             | attached board port  |
+--------------------------------------------------+-----------------------------+----------------------+
| ``make flash``                                   | ``.\neo.cmd flash``         | Build, verify and    |
|                                                  |                             | flash                |
+--------------------------------------------------+-----------------------------+----------------------+
| ``make monitor``                                 | ``.\neo.cmd monitor``       | Open the local       |
|                                                  |                             | interactive IDF      |
|                                                  |                             | monitor              |
+--------------------------------------------------+-----------------------------+----------------------+
| ``make flash-monitor`` / ``make full``           | ``.\neo.cmd flash-monitor`` | Build, flash and     |
|                                                  | / ``.\neo.cmd full``        | monitor              |
+--------------------------------------------------+-----------------------------+----------------------+
| ``make menuconfig``                              | ``.\neo.cmd menuconfig``    | Edit local ESP-IDF   |
|                                                  |                             | settings             |
+--------------------------------------------------+-----------------------------+----------------------+
| ``make clean``                                   | ``.\neo.cmd clean``         | Clean this project's |
|                                                  |                             | IDF build directory  |
+--------------------------------------------------+-----------------------------+----------------------+

``./neo build`` is also available on Ubuntu when Make is not installed. ``PORT`` can
override the saved port for a single invocation. On Ubuntu, the runner/user needs
``dialout`` membership for serial access; log in again after adding the group.
Monitoring remains interactive locally; exit with Ctrl+].

``baseline`` disables local overrides for later builds without deleting the file
or external checkout. ``dev MODULE=...`` enables the saved overrides again. It never
switches branches, discards changes, publishes releases or pushes Git commits.

Local state and environment isolation
-------------------------------------

- ``.workspace/dev-venv`` contains project Python dependencies.
- ``.workspace/developer.json`` remembers SDK paths, board port and selection mode.
- ``packages.local.yml`` contains live module mappings; ``packages.yml`` stays the
  committed baseline. ``ci_targets.yml`` in each module still controls GitHub CI.
- Fresh SDKs/tools are cached under ``~/.neotech/toolchains``, shared across projects
  by SDK version. Advanced users can set ``NEOTECH_TOOLCHAIN_DIR`` before setup to
  select another cache directory; an explicit override takes precedence over
  saved project settings. The old ``NEOCAM_TOOLCHAIN_DIR`` variable is accepted as
  a compatibility alias when the new variable is unset.
- Existing installations under ``~/.neocam/toolchains``, saved SDK paths or the
  workspace's ``../.toolchain`` remain reusable. They are not moved or deleted:
  Python virtual environments can contain absolute installation paths. Fresh
  installs use the neutral cache; finding an old valid install avoids downloading
  another SDK solely for a directory-name change.
- Existing ``IDF_PATH``/``IDF_TOOLS_PATH`` or workspace toolchains are reused only
  when the source tag matches v6.0.1. Shell environment changes affect child
  commands only; no persistent system PATH, Git configuration or pip settings
  are modified.
- Public Python dependencies use PyPI in the helper's child processes, isolated
  from saved pip index files. ``NEOCAM_PIP_INDEX`` can select an approved mirror;
  existing network proxy/certificate environment settings remain available.

``Ubuntu developer commands`` CI validates bootstrap on Ubuntu 24.04, ``make check``,
an incremental ``make build``, and environment discovery. It never flashes a board.

References:

- `ESP-IDF v6.0.1 installation <https://docs.espressif.com/projects/esp-idf/en/v6.0.1/esp32s3/get-started/index.html>`__.
- `IDF's installation/export helper <https://github.com/espressif/esp-idf/blob/v6.0.1/tools/idf_tools.py>`__.
- `SPI example Makefile <https://github.com/NeoTech-vietnam/NeoExamples-ESP32-FreeRTOS/blob/feature/spi/03_Interfaces-and-Protocols/01_Basic/03_SPI/00_validate_project/Makefile>`__.
