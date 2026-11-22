EA211 ownership model applied to NeoCam
=======================================

EA211's project repository supplies configuration, tools, tests and patches.
``conandata.yml`` declares consumed package references and destination directories.
Its cached common recipe copies package content into those destinations during
generation and writes local ignore files. Fetching does not turn those consumed
directories into the authoritative source repositories.

NeoCam retains that distinction. Its manifest instead selects Git repository
commits, avoiding a package server during active source development. Exported
snapshots appear directly at the project root, following MMD's component layout.
Native ESP-IDF manages the vendor camera/JPEG dependency graph separately.

Migration mapping
-----------------

+----------------------------------+----------------------------------+
| Original firmware area           | New owner                        |
+==================================+==================================+
| BSW/Infrastruc/CUCEL             | CUCEL repository                 |
+----------------------------------+----------------------------------+
| BSW/Infrastruc/BootCtrl          | BootCtrl repository              |
+----------------------------------+----------------------------------+
| BSW/Infrastruc/BswLib            | BswLib repository; MediaBuf      |
|                                  | subfolder retained               |
+----------------------------------+----------------------------------+
| BSW/SysSrv/EbOs, LocalTime       | EbOs and LocalTime repositories  |
+----------------------------------+----------------------------------+
| BSW/CDD/CamIo, CamPipe           | CamIo and CamPipe repositories   |
+----------------------------------+----------------------------------+
| BSW/ComStack/WifiStack/WifiIf,   | WifiStack repository             |
| WifiMgr                          |                                  |
+----------------------------------+----------------------------------+
| BSW/ComStack/WifiStack/HttpSrv   | HttpSrv repository               |
+----------------------------------+----------------------------------+
| Rte                              | Rte repository                   |
+----------------------------------+----------------------------------+
| ApplicationLayer                 | CamApp repository; ASW/ASV/DE    |
|                                  | subfolders retained              |
+----------------------------------+----------------------------------+
| STConf/GLOBAL                    | NeoContracts repository          |
+----------------------------------+----------------------------------+
| STConf/ConfAr and main/main.c    | Conf/\__CONFIG                   |
+----------------------------------+----------------------------------+
| STConf/CONFIG/CameraProfiles     | GConf/CameraProfiles             |
+----------------------------------+----------------------------------+
| STConf/CONFIG/MemMap_Conf        | Conf/CUCEL                       |
+----------------------------------+----------------------------------+
| Module product configuration     | Conf/module                      |
| values/macros                    |                                  |
+----------------------------------+----------------------------------+
| STConf/TOOLCONF                  | TOOLCONF                         |
+----------------------------------+----------------------------------+

Configuration contracts remain module-owned as ``CamIo_ConfigTypes.h``,
``WifiMgr_ConfigTypes.h``, and ``HttpSrv_ConfigTypes.h``. The product supplies their
values and tuning macros through Conf. Standard platform types remain unextended.
No public C type or function was renamed. Modules require their documented peer
headers and product configuration to build; independent ownership does not mean
they have no dependencies.

The retained IDF groups are BSW, Rte, ApplicationLayer and main. Their wrappers
live under TOOLCONF/esp-idf and read module-owned ``module.cmake`` source lists.
This avoids a behavior-changing build-graph rewrite during source separation.
Module tests for BootCtrl/NVS, Wi-Fi, and HTTP travel with those repositories.
Camera/buffer/pipeline/application integration tests and the host harness remain
in the integration project.

Fetched destination roots are ignored centrally. In live development mode the
fetcher never writes ``.gitignore`` files into linked source checkouts. Snapshot
fingerprints protect local changes; directory links are unlinked without
recursively removing the source target. Cache entries are not development folders.

The original projects are preserved. The bootstrap copies files; its source
commit and hashes are recorded in ``_metadata/source-mapping.json``. The one-time
bootstrap refuses to overwrite an existing destination. Original Git history is
referenced through provenance rather than rewritten into the new repositories.
