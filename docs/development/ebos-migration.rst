EbOs configuration and camera-worker pilot
==========================================

This milestone separates reusable OS mechanisms from product scheduling policy.
EbOs remains an independently maintained repository. NeoCam supplies typed C
configuration and task-entry wiring; ESP-IDF 6.0.1 supplies the kernel.

MMD architecture carried forward
--------------------------------

The MMD reference separates the OS/platform integration, reusable scheduling
adaptations, project ``Conf/EbOs`` inputs and generated runnable dispatch.
NeoCam adopts that ownership split with handwritten C configuration. MMD's
proprietary OS, generated task bodies, six-core configuration and SC3 selection
are architectural references, not imported implementation or guarantees.

.. list-table:: Ownership
   :header-rows: 1
   :widths: 26 74

   * - Owner
     - Responsibility
   * - EbOs repository
     - Portable interfaces, configuration types/validation, native task and
       synchronization mechanisms, lifecycle diagnostics and module tests.
   * - ``Conf/EbOs``
     - Concrete task stack/priority/affinity settings and entry-function wiring.
   * - CamPipe
     - Camera state machine, frame acquisition and cooperative stop request.
   * - ``Conf/__CONFIG``
     - Startup/shutdown composition and dependency order.
   * - ``sdkconfig.defaults``
     - Kernel and SDK build settings, including tick frequency.

EbOs accepts configuration through function arguments. It does not include
NeoCam configuration headers or reference camera/HTTP symbols. HTTP and Wi-Fi
execution remain unchanged in this pilot. SDK-owned camera, Wi-Fi and network
tasks remain SDK implementation details.

Project configuration
---------------------

``Conf/EbOs/EbOs_Cfg.h`` owns the camera worker's default stack size (8192 bytes)
and priority (5). It retains the existing ``NEOCAM_PRODUCER_CORE`` override:
``-1`` is unpinned; ``0`` or ``1`` selects an available ESP32-S3 core.
``Conf/EbOs/EbOs_Cfg.c`` supplies ``CamPipe_TaskConfig`` and the task entry that
repeatedly calls ``CamPipe_ProducerStep`` with an actual one-tick yield.

CamPipe declares its required configuration through ``CamPipe_TaskConfig.h``.
Its backend passes the supplied configuration to EbOs and uses the opaque task
handle for join/deletion and stack reporting. The old task-tuning macros in
``Conf/CamPipe`` are compatibility aliases to the new single source of policy.
Camera profile and operation-timeout settings remain in their existing owners.

Typed ``const`` C configuration does not require static task allocation. EbOs
uses ESP-IDF's native dynamic task creation in this milestone; changing memory
allocation policy would be a separate change.

Lifecycle and failure handling
------------------------------

.. code-block:: text

   existing NeoCam composition
      -> CamPipe_Start
      -> EbOs_TaskCreate(CamPipe_TaskConfig)
      -> native task runs project camera entry
      -> CamPipe requests cooperative stop
      -> entry returns after its current work finishes
      -> EbOs caches stack minimum, publishes completion and suspends
      -> owner joins, confirms suspension, deletes and clears handle

Create, join/deletion and stack sampling require a serialized owner. The task
entry must return cooperatively rather than deleting or suspending itself.
EbOs initializes metadata before native creation because a task can complete
before its creator resumes. Join waits for both completion and confirmed native
suspension; it never force-deletes unfinished work. A timeout preserves the task
handle and its dependencies for a later retry. This retains the existing
composition's retryable shutdown behavior.

An owner must not release camera resources after a failed join. The same task
handle remains valid for retry. Stack measurements use bytes and are sampled
only while lifecycle operations are serialized. They can use a stable native
handle both while running and after return. After completion EbOs takes the
lower of the entry-return snapshot and current native minimum so that the
suspension path's stack use is included. The native task stays alive until join.

AUTOSAR adaptation profile
--------------------------

The selected specification is `AUTOSAR Classic R25-11 OS, Document 34
<https://www.autosar.org/fileadmin/standards/R25-11/CP/AUTOSAR_CP_SWS_OS.pdf>`__.
The module's `compatibility matrix
<https://neotech-vietnam.github.io/EbOs/specification.html#sws-ebos-compatibility>`__
records the supported subset and missing semantics.

The current camera worker is a persistent, potentially blocking FreeRTOS
thread, not an AUTOSAR basic task. Native mutex priority inheritance does not
implement AUTOSAR resource priority ceiling (OS section 7.9.21). Typed task
configuration adopts the separation of policy described by ``OsTask``
(section 10.2.32), without asserting equivalent activation or scheduling rules.

ESP-IDF already starts FreeRTOS before ``app_main``. EbOs must not call
``vTaskStartScheduler`` / ``vTaskEndScheduler`` or present object initialization
as ``StartOS``. See the versioned `application entry-point documentation
<https://docs.espressif.com/projects/esp-idf/en/v6.0.1/esp32s3/api-reference/system/freertos.html#application-entry-point>`__
and `FreeRTOS task/affinity documentation
<https://docs.espressif.com/projects/esp-idf/en/v6.0.1/esp32s3/api-reference/system/freertos_idf.html>`__.

Later stages specify basic-task activation/termination, extended-task events,
alarms/counters and HTTP worker migration separately. Resources, schedule
tables, OS applications and memory/timing protection require a further
compatibility feasibility assessment. Future native timer callbacks should
only release work to tasks, as described in `ESP Timer 6.0.1
<https://docs.espressif.com/projects/esp-idf/en/v6.0.1/esp32s3/api-reference/system/esp_timer.html>`__.

Package selection and independent development
----------------------------------------------

The module's source and published documentation are independent of a product's
selected snapshot. ``ebos/1.0.0@neotech/prototype`` contains the earlier
mutex/delay interface; the camera pilot requires compatible EbOs, CamPipe and
integration-configuration revisions selected together.

For local EbOs development, run ``.\neo.cmd dev EbOs`` on Windows or
``make dev MODULE=EbOs`` on Ubuntu from the integration repository. This links
the external checkout through ignored local overrides. It does not change the
committed ``packages.yml`` baseline. Build with the compatible CamPipe checkout
or its selected snapshot and the matching integration configuration.

Publication follows dependency order: additive EbOs support first, then CamPipe
and the integration configuration selecting compatible revisions on the feature
branch. Existing exact-commit module dispatch continues to supply the pushed
EbOs SHA while other package revisions come from the project manifest. No
release tag needs to move for each development push. Promote the reviewed
combination through the normal manifest change and review process.

Verification and hardware gate
-------------------------------

From the EbOs repository, run:

.. code-block:: sh

   python test/run_host_tests.py

These tests compile the real implementation against a controlled native
backend. ``test/fixtures/second_project.c`` demonstrates another product's C
configuration using the same module. Coverage includes invalid configuration,
allocation failure, immediate completion, completion before suspension,
timeout/retry, repeated lifecycle operations, context errors and stack reporting.

From the integration repository, run ``.\neo.cmd check`` on Windows or
``make check`` on Ubuntu. The pilot adds backend/configuration coverage alongside
the existing camera, buffer, HTTP and Wi-Fi regressions and the ESP-IDF firmware
build. Strict Sphinx builds validate both documentation sets.

Host tests and firmware compilation do not prove cross-core context switching
or target timing. Hardware acceptance remains pending until an on-device run
records repeated dual-core start/stop, join timeout/retry, stack observations and
the normal camera stream/photo behavior. No hardware flashing is triggered by
the module host tests.

EbOs supplies a dedicated ``test/on_target`` acceptance app. Follow the module's
``test/README.md`` for its ESP-IDF 6.0.1 build and explicit flash/monitor commands.
The test exercises pinned and unpinned workers, repeated immediate completion,
timeout/retry and native heap retention. Record monitor output containing
``PASS EBOS_DUAL_CORE_LIFECYCLE``. This app replaces the camera firmware when
flashed, so normal NeoCam stream/photo behavior must be checked separately with
the product firmware. Compiling the test app does not constitute hardware
acceptance.
