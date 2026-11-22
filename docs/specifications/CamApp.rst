.. _sws-camapp:

Specification of CamApp
=======================

.. list-table:: Document metadata
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Document ID
     - ``NEOCAM-SWS-CamApp``
   * - Owner
     - NeoCam integration
   * - Status
     - Reference for the selected NeoCam release
   * - Selected ref
     - ``camapp/1.0.0@neotech/prototype``
   * - Source commit
     - `74ea4c09a6dd6a70146ea806e0a41822430f1f6c <https://github.com/NeoTech-vietnam/CamApp/tree/74ea4c09a6dd6a70146ea806e0a41822430f1f6c>`__

.. list-table:: Document change history
   :header-rows: 1

   * - Date
     - Revision
     - Description
   * - 2026-11-22
     - 1.0
     - Initial specification of the manifest-selected implementation.

.. contents:: Contents
   :local:
   :depth: 2

1 Introduction and functional overview
--------------------------------------

CamApp implements the camera dashboard, photo/profile supervision, diagnostic metrics and device-facing glue. The ASW, ASV and DE components use Rte ports to reach the camera services.

2 Acronyms and abbreviations
----------------------------

.. list-table:: Terminology
   :header-rows: 1

   * - Term
     - Meaning
   * - ASW
     - Application software.
   * - ASV
     - Application service.
   * - DE
     - Device encapsulation.
   * - HMI
     - Human-machine interface.

3 Related documentation
-----------------------

* :doc:`NeoCam architecture and adaptation profile <../architecture/architecture>`
* :doc:`../operations/runtime`
* :doc:`../validation/optimization`
* :doc:`Rte`

4 Constraints and assumptions
-----------------------------

* Application callbacks expect initialized Rte wiring. The HMI initialization takes a camera information snapshot.
* Borrowed frame descriptors used for diagnostics remain valid during the callback. Frame leases returned by capture must be released.
* A profile-change result reports admission. The pipeline owns completion and recovery.

5 Dependencies and file structure
---------------------------------

.. list-table:: Dependencies
   :header-rows: 1

   * - Dependency
     - Purpose
   * - :doc:`NeoContracts`
     - Defines frames, profiles, status and HTTP port types.
   * - :doc:`Rte`
     - Connects device and diagnostic services and provides synchronization and time.
   * - ``GConf/CameraProfiles/Neo_Profiles.c``
     - Supplies preset lookup and values used by the application.

**Source files**

`ASW/CamHmi/CamHmi.h <https://github.com/NeoTech-vietnam/CamApp/blob/74ea4c09a6dd6a70146ea806e0a41822430f1f6c/ASW/CamHmi/CamHmi.h>`__, `ASW/CamHmi/CamHmi.c <https://github.com/NeoTech-vietnam/CamApp/blob/74ea4c09a6dd6a70146ea806e0a41822430f1f6c/ASW/CamHmi/CamHmi.c>`__, `ASW/CamDiag/CamDiag.h <https://github.com/NeoTech-vietnam/CamApp/blob/74ea4c09a6dd6a70146ea806e0a41822430f1f6c/ASW/CamDiag/CamDiag.h>`__, `ASW/CamDiag/CamDiag.c <https://github.com/NeoTech-vietnam/CamApp/blob/74ea4c09a6dd6a70146ea806e0a41822430f1f6c/ASW/CamDiag/CamDiag.c>`__, `ASV/CamSupv/CamSupv.h <https://github.com/NeoTech-vietnam/CamApp/blob/74ea4c09a6dd6a70146ea806e0a41822430f1f6c/ASV/CamSupv/CamSupv.h>`__, `ASV/CamSupv/CamSupv.c <https://github.com/NeoTech-vietnam/CamApp/blob/74ea4c09a6dd6a70146ea806e0a41822430f1f6c/ASV/CamSupv/CamSupv.c>`__, `DE/CamDev/CamDev.h <https://github.com/NeoTech-vietnam/CamApp/blob/74ea4c09a6dd6a70146ea806e0a41822430f1f6c/DE/CamDev/CamDev.h>`__, `DE/CamDev/CamDev.c <https://github.com/NeoTech-vietnam/CamApp/blob/74ea4c09a6dd6a70146ea806e0a41822430f1f6c/DE/CamDev/CamDev.c>`__, `module.cmake <https://github.com/NeoTech-vietnam/CamApp/blob/74ea4c09a6dd6a70146ea806e0a41822430f1f6c/module.cmake>`__.

6 Requirements traceability
---------------------------

.. list-table:: Requirements traceability
   :header-rows: 1

   * - Requirement
     - Description
     - Satisfied by
     - Verification evidence
   * - ``NEOCAM-SWS-CamApp-001``
     - Compose the dashboard and route HTTP content into typed Rte ports.
     - :ref:`ASW CamHmi dashboard and content <sws-camapp-hmi>`
     - ``application`` host case in ``test/test_application.c``.
   * - ``NEOCAM-SWS-CamApp-002``
     - Collect capture and stream metrics with serialized updates.
     - :ref:`ASW CamDiag diagnostics <sws-camapp-diagnostics>`
     - ``test/test_application.c`` and :doc:`metrics definitions <../validation/optimization>`.
   * - ``NEOCAM-SWS-CamApp-003``
     - Accept named preview presets and expose progress.
     - :ref:`ASV CamSupv profile and still capture <sws-camapp-supervisor>`
     - `ASV/CamSupv/CamSupv.c <https://github.com/NeoTech-vietnam/CamApp/blob/74ea4c09a6dd6a70146ea806e0a41822430f1f6c/ASV/CamSupv/CamSupv.c>`__ and ``test/test_application.c``.
   * - ``NEOCAM-SWS-CamApp-004``
     - Forward camera access using the typed Rte surface.
     - :ref:`DE CamDev device access <sws-camapp-device>`
     - `DE/CamDev/CamDev.c <https://github.com/NeoTech-vietnam/CamApp/blob/74ea4c09a6dd6a70146ea806e0a41822430f1f6c/DE/CamDev/CamDev.c>`__ and ``test/test_application.c``.

7 Functional specification
--------------------------

.. _sws-camapp-hmi:

ASW CamHmi dashboard and content
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The HMI uses initialized camera details for dashboard generation. It exposes callbacks for latest preview, streaming, photo and profile operations. It forwards releases through Rte and reports capture outcomes to diagnostics.

.. _sws-camapp-diagnostics:

ASW CamDiag diagnostics
~~~~~~~~~~~~~~~~~~~~~~~

The diagnostics mutex protects counters and the sample window. Successful stream frames update send timing and skipped sequence statistics. A new epoch resets the sample window. JSON combines a local snapshot with available pipeline statistics.

.. _sws-camapp-supervisor:

ASV CamSupv profile and still capture
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

CamSupv resolves exact preset names, rejects the photo-only preset for preview selection, and forwards the selected ID. The photo callback invokes the dedicated pipeline service. Profile JSON reports current state, estimates and available presets.

.. _sws-camapp-device:

DE CamDev device access
~~~~~~~~~~~~~~~~~~~~~~~

CamDev delegates capture, release, current camera information, and newer-frame acquisition to the corresponding Rte camera services.

Error classification
~~~~~~~~~~~~~~~~~~~~

Invalid names and invalid output parameters can report ``NEO_E_PARAM``. Bounded text outputs return ``NEO_E_TOO_LARGE`` if the destination is insufficient. Device and supervisor calls propagate the selected service status.

8 API specification
-------------------

ASW CamHmi
~~~~~~~~~~

.. list-table:: CamHmi_HttpPorts
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Name
     - ``CamHmi_HttpPorts``
   * - Kind
     - ``const Neo_HttpPortsType``
   * - Description
     - Static table of dashboard, metrics, capture, stream, photo, profile and lease callbacks.
   * - Available via
     - ``CamHmi.h``

.. list-table:: CamHmi_Init
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``CamHmi_Init``
   * - Syntax
     - ``Neo_StatusType CamHmi_Init(void)``
   * - Execution and reentrancy
     - Synchronous. The composition owner serializes initialization and shutdown.
   * - Parameters (in)
     - None.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - None.
   * - Return value
     - Propagates the Rte service result.
   * - Description
     - Reads device information, then initializes the diagnostics snapshot.
   * - Available via
     - ``CamHmi.h``

.. list-table:: CamHmi_Deinit
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``CamHmi_Deinit``
   * - Syntax
     - ``Neo_StatusType CamHmi_Deinit(void)``
   * - Execution and reentrancy
     - Synchronous. The composition owner serializes initialization and shutdown.
   * - Parameters (in)
     - None.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - None.
   * - Return value
     - ``NEO_OK``
   * - Description
     - Ends the configured application stage.
   * - Available via
     - ``CamHmi.h``

ASW CamDiag
~~~~~~~~~~~

.. list-table:: CamDiag_Init
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``CamDiag_Init``
   * - Syntax
     - ``void CamDiag_Init(const Neo_CameraInfoType *info)``
   * - Execution and reentrancy
     - Synchronous task-context call. Shared metric state is protected by the Rte diagnostics mutex.
   * - Parameters (in)
     - ``info`` non-null camera data.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - None.
   * - Return value
     - None.
   * - Description
     - Resets state and records initial dimensions.
   * - Available via
     - ``CamDiag.h``

.. list-table:: CamDiag_Captured
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``CamDiag_Captured``
   * - Syntax
     - ``void CamDiag_Captured(const Neo_FrameType *frame)``
   * - Execution and reentrancy
     - Synchronous task-context call. Shared metric state is protected by the Rte diagnostics mutex.
   * - Parameters (in)
     - ``frame`` non-null borrowed descriptor.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - None.
   * - Return value
     - None.
   * - Description
     - Records capture duration, size and dimensions and counts still photos.
   * - Available via
     - ``CamDiag.h``

.. list-table:: CamDiag_Failed
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``CamDiag_Failed``
   * - Syntax
     - ``void CamDiag_Failed(void)``
   * - Execution and reentrancy
     - Synchronous task-context call. Shared metric state is protected by the Rte diagnostics mutex.
   * - Parameters (in)
     - None.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - None.
   * - Return value
     - None.
   * - Description
     - Increments the application failure count.
   * - Available via
     - ``CamDiag.h``

.. list-table:: CamDiag_StreamOpened
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``CamDiag_StreamOpened``
   * - Syntax
     - ``void CamDiag_StreamOpened(void)``
   * - Execution and reentrancy
     - Synchronous task-context call. Shared metric state is protected by the Rte diagnostics mutex.
   * - Parameters (in)
     - None.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - None.
   * - Return value
     - None.
   * - Description
     - Records the start timestamp upon the first stream opening after initialization.
   * - Available via
     - ``CamDiag.h``

.. list-table:: CamDiag_StreamFrame
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``CamDiag_StreamFrame``
   * - Syntax
     - ``void CamDiag_StreamFrame(const Neo_FrameType *frame, boolean sent, uint32 send_us)``
   * - Execution and reentrancy
     - Synchronous task-context call. Shared metric state is protected by the Rte diagnostics mutex.
   * - Parameters (in)
     - ``frame`` non-null descriptor, ``sent`` outcome and ``send_us`` send duration.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - None.
   * - Return value
     - None.
   * - Description
     - Updates frame properties. Successful sends contribute cadence, delay and sequence samples.
   * - Available via
     - ``CamDiag.h``

.. list-table:: CamDiag_GetJson
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``CamDiag_GetJson``
   * - Syntax
     - ``Neo_StatusType CamDiag_GetJson(char *text, uint32 capacity, uint32 *length)``
   * - Execution and reentrancy
     - Synchronous task-context call. Shared metric state is protected by the Rte diagnostics mutex.
   * - Parameters (in)
     - ``capacity`` destination bytes.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - ``text`` JSON buffer and ``length`` bytes written.
   * - Return value
     - ``NEO_OK``, ``NEO_E_PARAM``, ``NEO_E_TOO_LARGE``
   * - Description
     - Serializes the diagnostics snapshot and available pipeline statistics.
   * - Available via
     - ``CamDiag.h``

ASV CamSupv
~~~~~~~~~~~

.. list-table:: CamSupv_SelectProfile
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``CamSupv_SelectProfile``
   * - Syntax
     - ``Neo_StatusType CamSupv_SelectProfile(const char *name)``
   * - Execution and reentrancy
     - Asynchronous profile change. The pipeline serializes command admission.
   * - Parameters (in)
     - ``name`` NUL-terminated preview preset name.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - None.
   * - Return value
     - ``NEO_E_PARAM`` for an invalid preset. Otherwise the Rte result.
   * - Description
     - Validates the name and forwards the selected profile ID.
   * - Available via
     - ``CamSupv.h``

.. list-table:: CamSupv_Photo
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``CamSupv_Photo``
   * - Syntax
     - ``Neo_StatusType CamSupv_Photo(Neo_FrameType *frame)``
   * - Execution and reentrancy
     - Synchronous forwarding. Reentrancy follows the Rte provider contract.
   * - Parameters (in)
     - None.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - ``frame`` JPEG descriptor with one lease on success.
   * - Return value
     - ``NEO_E_PARAM`` for null output. Otherwise the Rte result.
   * - Description
     - Requests the dedicated still capture operation.
   * - Available via
     - ``CamSupv.h``

.. list-table:: CamSupv_ProfileJson
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``CamSupv_ProfileJson``
   * - Syntax
     - ``Neo_StatusType CamSupv_ProfileJson(char *text, uint32 capacity, uint32 *length)``
   * - Execution and reentrancy
     - Synchronous forwarding. Reentrancy follows the Rte provider contract.
   * - Parameters (in)
     - ``capacity`` destination bytes.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - ``text`` JSON buffer and ``length`` bytes written.
   * - Return value
     - ``NEO_OK``, ``NEO_E_PARAM``, ``NEO_E_TOO_LARGE`` May propagate a pipeline statistics error.
   * - Description
     - Serializes the state, profile settings and errors.
   * - Available via
     - ``CamSupv.h``

DE CamDev
~~~~~~~~~

.. list-table:: CamDev_Capture
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``CamDev_Capture``
   * - Syntax
     - ``Neo_StatusType CamDev_Capture(Neo_FrameType *frame)``
   * - Execution and reentrancy
     - Synchronous forwarding. Reentrancy follows the Rte provider contract.
   * - Parameters (in)
     - None.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - ``frame`` JPEG descriptor with one lease on success.
   * - Return value
     - Propagates the Rte service result.
   * - Description
     - Requests the latest available preview frame.
   * - Available via
     - ``CamDev.h``

.. list-table:: CamDev_Release
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``CamDev_Release``
   * - Syntax
     - ``Neo_StatusType CamDev_Release(Neo_BufferTokenType token)``
   * - Execution and reentrancy
     - Synchronous forwarding. Reentrancy follows the Rte provider contract.
   * - Parameters (in)
     - ``token`` live lease.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - None.
   * - Return value
     - Propagates the Rte service result.
   * - Description
     - Releases one buffer reference.
   * - Available via
     - ``CamDev.h``

.. list-table:: CamDev_GetInfo
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``CamDev_GetInfo``
   * - Syntax
     - ``Neo_StatusType CamDev_GetInfo(Neo_CameraInfoType *info)``
   * - Execution and reentrancy
     - Synchronous forwarding. Reentrancy follows the Rte provider contract.
   * - Parameters (in)
     - None.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - ``info`` camera details.
   * - Return value
     - Propagates the Rte service result.
   * - Description
     - Reads camera model information and dimensions.
   * - Available via
     - ``CamDev.h``

.. list-table:: CamDev_Next
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``CamDev_Next``
   * - Syntax
     - ``Neo_StatusType CamDev_Next(uint64 after_sequence, uint32 timeout_ms, Neo_FrameType *frame)``
   * - Execution and reentrancy
     - Synchronous forwarding. Reentrancy follows the Rte provider contract.
   * - Parameters (in)
     - ``after_sequence`` exclusive lower bound, ``timeout_ms`` wait limit.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - ``frame`` JPEG descriptor with one lease on success.
   * - Return value
     - Propagates the Rte service result.
   * - Description
     - Requests a newer preview publication.
   * - Available via
     - ``CamDev.h``

9 Sequence diagrams
-------------------

:ref:`The product sequence diagrams <neocam-runtime-sequences>` show application dispatch through Rte. CamSupv reports request admission and the browser may query profile state while the pipeline works.

10 Configuration specification
------------------------------

.. list-table:: Diagnostics sample window
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Owner
     - ``CamApp/ASW/CamDiag/CamDiag.c``
   * - Type
     - Unsigned implementation constant
   * - Default
     - 64 recent samples.
   * - Units or allowed values
     - Sample count for send time, frame age and interval estimates.
   * - Effective
     - At firmware build time.

.. list-table:: Visible product presets
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Owner
     - ``GConf/CameraProfiles/Neo_Profiles.c``
   * - Type
     - ``Neo_ProfileType`` preset table
   * - Default
     - The integration defaults described in :doc:`CamPipe`.
   * - Units or allowed values
     - Preview-only selection. Photo is exposed as a dedicated action.
   * - Effective
     - When the firmware is built and the dashboard or profile status reads the table.
