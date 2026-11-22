.. _sws-rte:

Specification of Rte
====================

.. list-table:: Document metadata
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Document ID
     - ``NEOCAM-SWS-Rte``
   * - Owner
     - NeoCam integration
   * - Status
     - Reference for the selected NeoCam release
   * - Selected ref
     - ``rte/1.0.0@neotech/prototype``
   * - Source commit
     - `3cf108c30ee6cfe30158601787333abb51fea2d8 <https://github.com/NeoTech-vietnam/Rte/tree/3cf108c30ee6cfe30158601787333abb51fea2d8>`__

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

Rte is the hand-written runtime wiring for NeoCam. It connects HTTP, application, and device adapters using typed function pointers and exposes camera-service forwarding and diagnostic locking.

2 Acronyms and abbreviations
----------------------------

.. list-table:: Terminology
   :header-rows: 1

   * - Term
     - Meaning
   * - RTE
     - Run-time environment.
   * - Provider port
     - Prewired callback table supplied by a component.

3 Related documentation
-----------------------

* :doc:`NeoCam architecture and adaptation profile <../architecture/architecture>`
* :doc:`../operations/runtime`
* :doc:`CamApp`
* :doc:`HttpSrv`

4 Constraints and assumptions
-----------------------------

* Use configured ports only during the initialized lifetime. Composition quiesces callers before deinitialization.
* Diagnostic callers must pair entry and exit on the same task.
* Buffer ownership is defined by the provider and carried through forwarding.

5 Dependencies and file structure
---------------------------------

.. list-table:: Dependencies
   :header-rows: 1

   * - Dependency
     - Purpose
   * - :doc:`NeoContracts`
     - Defines shared types and the HTTP callbacks.
   * - :doc:`CamIo`
     - Provides camera information.
   * - :doc:`CamPipe`
     - Provides frame, profile, photo and statistics services.
   * - :doc:`EbOs`
     - Manages the diagnostic mutex.
   * - :doc:`LocalTime`
     - Provides elapsed time for diagnostics.

**Source files**

`Rte.h <https://github.com/NeoTech-vietnam/Rte/blob/3cf108c30ee6cfe30158601787333abb51fea2d8/Rte.h>`__, `Rte.c <https://github.com/NeoTech-vietnam/Rte/blob/3cf108c30ee6cfe30158601787333abb51fea2d8/Rte.c>`__, `module.cmake <https://github.com/NeoTech-vietnam/Rte/blob/3cf108c30ee6cfe30158601787333abb51fea2d8/module.cmake>`__.

6 Requirements traceability
---------------------------

.. list-table:: Requirements traceability
   :header-rows: 1

   * - Requirement
     - Description
     - Satisfied by
     - Verification evidence
   * - ``NEOCAM-SWS-Rte-001``
     - Validate and copy a complete set of provider tables.
     - :ref:`Static port wiring <sws-rte-wiring>`
     - ``application`` host case in ``test/test_application.c``.
   * - ``NEOCAM-SWS-Rte-002``
     - Forward service status and serialize diagnostics through a dedicated lock.
     - :ref:`Provider forwarding and diagnostic access <sws-rte-forwarding>`
     - ``application`` host case in ``test/test_application.c``. and `Rte.c <https://github.com/NeoTech-vietnam/Rte/blob/3cf108c30ee6cfe30158601787333abb51fea2d8/Rte.c>`__

7 Functional specification
--------------------------

.. _sws-rte-wiring:

Static port wiring
~~~~~~~~~~~~~~~~~~

Initialization validates every required callback and allocates the diagnostics mutex before copying provider tables. The returned HTTP table forwards into those tables. Composition stops users before deinitialization clears the bindings.

.. _sws-rte-forwarding:

Provider forwarding and diagnostic access
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The device, camera and supervisor wrappers forward to either configured callbacks or BSW service functions. Diagnostic notification wrappers check for a bound callback. Application diagnostics explicitly lock and unlock around shared state access.

Error classification
~~~~~~~~~~~~~~~~~~~~

Initialization rejects missing callbacks and repeated activation. Guarded status-returning wrappers return ``NEO_E_NOT_READY`` when unbound. Errors from the called provider otherwise propagate.

8 API specification
-------------------

Port table types
~~~~~~~~~~~~~~~~

.. list-table:: Rte_DevicePortsType
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Name
     - ``Rte_DevicePortsType``
   * - Kind
     - Function-pointer structure
   * - Representation / range
     - ``capture``, ``release``, ``info``, ``next``.
   * - Description
     - Application device services.
   * - Available via
     - ``Rte.h``

.. list-table:: Rte_DiagnosticPortsType
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Name
     - ``Rte_DiagnosticPortsType``
   * - Kind
     - Function-pointer structure
   * - Representation / range
     - ``init``, ``captured``, ``failed``, ``opened``, ``streamed``, ``json``.
   * - Description
     - Lifecycle and metrics callbacks.
   * - Available via
     - ``Rte.h``

.. list-table:: Rte_SupervisorPortsType
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Name
     - ``Rte_SupervisorPortsType``
   * - Kind
     - Function-pointer structure
   * - Representation / range
     - ``select_profile``, ``photo``, ``profile_json``.
   * - Description
     - Profile and photo services.
   * - Available via
     - ``Rte.h``

Lifecycle and HTTP wiring
~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table:: Rte_Init
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``Rte_Init``
   * - Syntax
     - ``Neo_StatusType Rte_Init(const Neo_HttpPortsType *application, const Rte_DevicePortsType *device, const Rte_DiagnosticPortsType *diagnostics, const Rte_SupervisorPortsType *supervisor)``
   * - Execution and reentrancy
     - Synchronous. Serialized by the composition owner.
   * - Parameters (in)
     - Four complete provider tables copied on success.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - None.
   * - Return value
     - ``NEO_OK``, ``NEO_E_PARAM``, ``NEO_E_STATE``, ``NEO_E_MEMORY``
   * - Description
     - Validates wiring and creates the diagnostics mutex.
   * - Available via
     - ``Rte.h``

.. list-table:: Rte_Deinit
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``Rte_Deinit``
   * - Syntax
     - ``Neo_StatusType Rte_Deinit(void)``
   * - Execution and reentrancy
     - Synchronous. Serialized by the composition owner.
   * - Parameters (in)
     - None.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - None.
   * - Return value
     - ``NEO_OK``
   * - Description
     - Releases the diagnostics mutex and clears provider tables.
   * - Available via
     - ``Rte.h``

.. list-table:: Rte_GetHttpPorts
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``Rte_GetHttpPorts``
   * - Syntax
     - ``const Neo_HttpPortsType * Rte_GetHttpPorts(void)``
   * - Execution and reentrancy
     - Synchronous. Serialized by the composition owner.
   * - Parameters (in)
     - None.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - None.
   * - Return value
     - ``const Neo_HttpPortsType *`` or null when disconnected.
   * - Description
     - Returns the wired HTTP adapter table.
   * - Available via
     - ``Rte.h``

Camera and device ports
~~~~~~~~~~~~~~~~~~~~~~~

.. list-table:: Rte_CameraCapture
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``Rte_CameraCapture``
   * - Syntax
     - ``Neo_StatusType Rte_CameraCapture(Neo_FrameType *frame)``
   * - Execution and reentrancy
     - Synchronous forwarding. The selected provider controls execution and reentrancy. Call while the wiring is live.
   * - Parameters (in)
     - None.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - ``frame`` output descriptor. A successful capture transfers one lease.
   * - Return value
     - The provider result, or ``NEO_E_NOT_READY`` when disconnected.
   * - Description
     - Waits up to 1000 ms for a frame newer than sequence zero.
   * - Available via
     - ``Rte.h``

.. list-table:: Rte_CameraRelease
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``Rte_CameraRelease``
   * - Syntax
     - ``Neo_StatusType Rte_CameraRelease(Neo_BufferTokenType token)``
   * - Execution and reentrancy
     - Synchronous forwarding. The selected provider controls execution and reentrancy. Call while the wiring is live.
   * - Parameters (in)
     - ``token`` lease to release.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - None.
   * - Return value
     - The provider result, or ``NEO_E_NOT_READY`` when disconnected.
   * - Description
     - Calls CamPipe to return a lease.
   * - Available via
     - ``Rte.h``

.. list-table:: Rte_CameraInfo
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``Rte_CameraInfo``
   * - Syntax
     - ``Neo_StatusType Rte_CameraInfo(Neo_CameraInfoType *info)``
   * - Execution and reentrancy
     - Synchronous forwarding. The selected provider controls execution and reentrancy. Call while the wiring is live.
   * - Parameters (in)
     - None.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - ``info`` camera details.
   * - Return value
     - The provider result, or ``NEO_E_NOT_READY`` when disconnected.
   * - Description
     - Calls CamIo for device information.
   * - Available via
     - ``Rte.h``

.. list-table:: Rte_CameraNext
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``Rte_CameraNext``
   * - Syntax
     - ``Neo_StatusType Rte_CameraNext(uint64 after_sequence, uint32 timeout_ms, Neo_FrameType *frame)``
   * - Execution and reentrancy
     - Synchronous forwarding. The selected provider controls execution and reentrancy. Call while the wiring is live.
   * - Parameters (in)
     - ``after_sequence`` exclusive lower bound and ``timeout_ms`` wait limit.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - ``frame`` output descriptor. A successful capture transfers one lease.
   * - Return value
     - The provider result, or ``NEO_E_NOT_READY`` when disconnected.
   * - Description
     - Calls CamPipe for a strictly newer frame.
   * - Available via
     - ``Rte.h``

.. list-table:: Rte_CameraPhoto
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``Rte_CameraPhoto``
   * - Syntax
     - ``Neo_StatusType Rte_CameraPhoto(Neo_FrameType *frame)``
   * - Execution and reentrancy
     - Synchronous forwarding. The selected provider controls execution and reentrancy. Call while the wiring is live.
   * - Parameters (in)
     - None.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - ``frame`` output descriptor. A successful capture transfers one lease.
   * - Return value
     - The provider result, or ``NEO_E_NOT_READY`` when disconnected.
   * - Description
     - Calls CamPipe for a still image.
   * - Available via
     - ``Rte.h``

.. list-table:: Rte_CameraRequestProfile
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``Rte_CameraRequestProfile``
   * - Syntax
     - ``Neo_StatusType Rte_CameraRequestProfile(Neo_ProfileIdType profile)``
   * - Execution and reentrancy
     - Asynchronous change. The admission call returns the CamPipe status.
   * - Parameters (in)
     - ``profile`` requested preset.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - None.
   * - Return value
     - The provider result, or ``NEO_E_NOT_READY`` when disconnected.
   * - Description
     - Calls CamPipe to enqueue a profile change.
   * - Available via
     - ``Rte.h``

.. list-table:: Rte_CameraStats
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``Rte_CameraStats``
   * - Syntax
     - ``Neo_StatusType Rte_CameraStats(Neo_PipelineStatsType *stats)``
   * - Execution and reentrancy
     - Synchronous forwarding. The selected provider controls execution and reentrancy. Call while the wiring is live.
   * - Parameters (in)
     - None.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - ``stats`` pipeline and resource snapshot.
   * - Return value
     - The provider result, or ``NEO_E_NOT_READY`` when disconnected.
   * - Description
     - Reads CamPipe statistics.
   * - Available via
     - ``Rte.h``

.. list-table:: Rte_DeviceCapture
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``Rte_DeviceCapture``
   * - Syntax
     - ``Neo_StatusType Rte_DeviceCapture(Neo_FrameType *frame)``
   * - Execution and reentrancy
     - Synchronous forwarding. The selected provider controls execution and reentrancy. Call while the wiring is live.
   * - Parameters (in)
     - None.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - ``frame`` output descriptor. A successful capture transfers one lease.
   * - Return value
     - The provider result, or ``NEO_E_NOT_READY`` when disconnected.
   * - Description
     - Invokes the configured device capture callback.
   * - Available via
     - ``Rte.h``

.. list-table:: Rte_DeviceRelease
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``Rte_DeviceRelease``
   * - Syntax
     - ``Neo_StatusType Rte_DeviceRelease(Neo_BufferTokenType token)``
   * - Execution and reentrancy
     - Synchronous forwarding. The selected provider controls execution and reentrancy. Call while the wiring is live.
   * - Parameters (in)
     - ``token`` lease to release.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - None.
   * - Return value
     - The provider result, or ``NEO_E_NOT_READY`` when disconnected.
   * - Description
     - Invokes the configured device release callback.
   * - Available via
     - ``Rte.h``

.. list-table:: Rte_DeviceInfo
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``Rte_DeviceInfo``
   * - Syntax
     - ``Neo_StatusType Rte_DeviceInfo(Neo_CameraInfoType *info)``
   * - Execution and reentrancy
     - Synchronous forwarding. The selected provider controls execution and reentrancy. Call while the wiring is live.
   * - Parameters (in)
     - None.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - ``info`` camera details.
   * - Return value
     - The provider result, or ``NEO_E_NOT_READY`` when disconnected.
   * - Description
     - Invokes the configured device info callback.
   * - Available via
     - ``Rte.h``

.. list-table:: Rte_DeviceNext
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``Rte_DeviceNext``
   * - Syntax
     - ``Neo_StatusType Rte_DeviceNext(uint64 after_sequence, uint32 timeout_ms, Neo_FrameType *frame)``
   * - Execution and reentrancy
     - Synchronous forwarding. The selected provider controls execution and reentrancy. Call while the wiring is live.
   * - Parameters (in)
     - ``after_sequence`` exclusive lower bound and ``timeout_ms`` wait limit.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - ``frame`` output descriptor. A successful capture transfers one lease.
   * - Return value
     - The provider result, or ``NEO_E_NOT_READY`` when disconnected.
   * - Description
     - Invokes the configured next-frame callback.
   * - Available via
     - ``Rte.h``

Supervisor and diagnostic ports
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table:: Rte_SelectProfile
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``Rte_SelectProfile``
   * - Syntax
     - ``Neo_StatusType Rte_SelectProfile(const char *name)``
   * - Execution and reentrancy
     - The call forwards acceptance of an asynchronous change.
   * - Parameters (in)
     - ``name`` profile name.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - None.
   * - Return value
     - The provider result, or ``NEO_E_NOT_READY`` when disconnected.
   * - Description
     - Forwards a profile selection.
   * - Available via
     - ``Rte.h``

.. list-table:: Rte_Photo
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``Rte_Photo``
   * - Syntax
     - ``Neo_StatusType Rte_Photo(Neo_FrameType *frame)``
   * - Execution and reentrancy
     - Synchronous forwarding. The selected provider controls execution and reentrancy. Call while the wiring is live.
   * - Parameters (in)
     - None.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - ``frame`` output descriptor. A successful capture transfers one lease.
   * - Return value
     - The provider result, or ``NEO_E_NOT_READY`` when disconnected.
   * - Description
     - Invokes the configured photo callback.
   * - Available via
     - ``Rte.h``

.. list-table:: Rte_ProfileJson
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``Rte_ProfileJson``
   * - Syntax
     - ``Neo_StatusType Rte_ProfileJson(char *text, uint32 capacity, uint32 *length)``
   * - Execution and reentrancy
     - Synchronous forwarding. The selected provider controls execution and reentrancy. Call while the wiring is live.
   * - Parameters (in)
     - ``capacity`` destination capacity in bytes.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - ``text`` JSON destination and ``length`` bytes written.
   * - Return value
     - The provider result, or ``NEO_E_NOT_READY`` when disconnected.
   * - Description
     - Invokes the profile JSON callback.
   * - Available via
     - ``Rte.h``

.. list-table:: Rte_DiagInit
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``Rte_DiagInit``
   * - Syntax
     - ``void Rte_DiagInit(const Neo_CameraInfoType *info)``
   * - Execution and reentrancy
     - Synchronous forwarding. The selected provider controls execution and reentrancy. Call while the wiring is live.
   * - Parameters (in)
     - ``info`` device details.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - None.
   * - Return value
     - None.
   * - Description
     - Initializes application diagnostics. Does nothing when its callback is disconnected.
   * - Available via
     - ``Rte.h``

.. list-table:: Rte_DiagCaptured
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``Rte_DiagCaptured``
   * - Syntax
     - ``void Rte_DiagCaptured(const Neo_FrameType *frame)``
   * - Execution and reentrancy
     - Synchronous forwarding. The selected provider controls execution and reentrancy. Call while the wiring is live.
   * - Parameters (in)
     - ``frame`` borrowed descriptor.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - None.
   * - Return value
     - None.
   * - Description
     - Records a captured frame. Does nothing when its callback is disconnected.
   * - Available via
     - ``Rte.h``

.. list-table:: Rte_DiagFailed
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``Rte_DiagFailed``
   * - Syntax
     - ``void Rte_DiagFailed(void)``
   * - Execution and reentrancy
     - Synchronous forwarding. The selected provider controls execution and reentrancy. Call while the wiring is live.
   * - Parameters (in)
     - None.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - None.
   * - Return value
     - None.
   * - Description
     - Records a capture failure. Does nothing when its callback is disconnected.
   * - Available via
     - ``Rte.h``

.. list-table:: Rte_DiagOpened
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``Rte_DiagOpened``
   * - Syntax
     - ``void Rte_DiagOpened(void)``
   * - Execution and reentrancy
     - Synchronous forwarding. The selected provider controls execution and reentrancy. Call while the wiring is live.
   * - Parameters (in)
     - None.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - None.
   * - Return value
     - None.
   * - Description
     - Records stream opening. Does nothing when its callback is disconnected.
   * - Available via
     - ``Rte.h``

.. list-table:: Rte_DiagStreamed
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``Rte_DiagStreamed``
   * - Syntax
     - ``void Rte_DiagStreamed(const Neo_FrameType *frame, boolean sent, uint32 send_us)``
   * - Execution and reentrancy
     - Synchronous forwarding. The selected provider controls execution and reentrancy. Call while the wiring is live.
   * - Parameters (in)
     - ``frame`` descriptor, ``sent`` outcome and ``send_us`` elapsed send time.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - None.
   * - Return value
     - None.
   * - Description
     - Records stream delivery. Does nothing when its callback is disconnected.
   * - Available via
     - ``Rte.h``

.. list-table:: Rte_DiagJson
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``Rte_DiagJson``
   * - Syntax
     - ``Neo_StatusType Rte_DiagJson(char *text, uint32 capacity, uint32 *length)``
   * - Execution and reentrancy
     - Synchronous forwarding. The selected provider controls execution and reentrancy. Call while the wiring is live.
   * - Parameters (in)
     - ``capacity`` destination capacity in bytes.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - ``text`` JSON destination and ``length`` bytes written.
   * - Return value
     - The provider result, or ``NEO_E_NOT_READY`` when disconnected.
   * - Description
     - Invokes the metrics JSON callback.
   * - Available via
     - ``Rte.h``

.. list-table:: Rte_TimeUs
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``Rte_TimeUs``
   * - Syntax
     - ``uint64 Rte_TimeUs(void)``
   * - Execution and reentrancy
     - Synchronous timer read.
   * - Parameters (in)
     - None.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - None.
   * - Return value
     - ``uint64`` elapsed microseconds.
   * - Description
     - Reads the local timer.
   * - Available via
     - ``Rte.h``

.. list-table:: Rte_EnterDiagnostics
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``Rte_EnterDiagnostics``
   * - Syntax
     - ``void Rte_EnterDiagnostics(void)``
   * - Execution and reentrancy
     - Synchronous. Task context with initialized wiring.
   * - Parameters (in)
     - None.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - None.
   * - Return value
     - None.
   * - Description
     - Takes the diagnostics mutex for an indefinite wait.
   * - Available via
     - ``Rte.h``

.. list-table:: Rte_ExitDiagnostics
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``Rte_ExitDiagnostics``
   * - Syntax
     - ``void Rte_ExitDiagnostics(void)``
   * - Execution and reentrancy
     - Synchronous. Called by the task holding the lock.
   * - Parameters (in)
     - None.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - None.
   * - Return value
     - None.
   * - Description
     - Releases the diagnostics mutex.
   * - Available via
     - ``Rte.h``

9 Sequence diagrams
-------------------

#. Composition passes the application, device, diagnostics and supervisor tables to Rte_Init.
#. HttpSrv receives the adapter table. Calls travel from its handlers or workers through Rte into the configured application callbacks.
#. The camera application reaches BSW services through the camera wrappers. Shutdown quiesces HttpSrv before disconnecting the tables.

10 Configuration specification
------------------------------

.. list-table:: Static provider bindings
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Owner
     - ``Conf/__CONFIG/NeoCam_Composition.c``
   * - Type
     - Typed constant function-pointer tables
   * - Default
     - CamHmi HTTP ports, CamDev device ports, CamDiag diagnostic ports, CamSupv supervisor ports.
   * - Units or allowed values
     - Each required callback must be non-null. The same table types describe the inputs to ``Rte_Init``.
   * - Effective
     - Compiled into the firmware and applied when the service starts.
