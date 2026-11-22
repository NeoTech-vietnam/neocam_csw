.. _sws-campipe:

Specification of CamPipe
========================

.. list-table:: Document metadata
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Document ID
     - ``NEOCAM-SWS-CamPipe``
   * - Owner
     - NeoCam integration
   * - Status
     - Reference for the selected NeoCam release
   * - Selected ref
     - ``campipe/1.0.0@neotech/prototype``
   * - Source commit
     - `f0fb17c375ce171536473147a76a9999643df4a3 <https://github.com/NeoTech-vietnam/CamPipe/tree/f0fb17c375ce171536473147a76a9999643df4a3>`__

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

CamPipe owns preview publication, profile transitions and still-photo capture sequencing. Its single producer acquires through CamIo and hands clients leases on immutable JPEG payloads.

2 Acronyms and abbreviations
----------------------------

.. list-table:: Terminology
   :header-rows: 1

   * - Term
     - Meaning
   * - JPEG
     - Encoded image payload.
   * - Lease
     - One retained reference to a MediaBuf token.
   * - Profile epoch
     - Counter identifying a camera profile activation.
   * - p95
     - 95th percentile of recent timing samples.

3 Related documentation
-----------------------

* :doc:`NeoCam architecture and adaptation profile <../architecture/architecture>`
* :doc:`../operations/runtime`
* :doc:`../validation/optimization`

4 Constraints and assumptions
-----------------------------

* Use the API from task context. Serialize Start and Stop and quiesce clients before dependency teardown.
* A retained frame requires one Release. Use its payload only while that reference is held.
* Profile requests accept preview profiles. Photo mode is entered through the dedicated photo operation.

5 Dependencies and file structure
---------------------------------

.. list-table:: Dependencies
   :header-rows: 1

   * - Dependency
     - Purpose
   * - :doc:`CamIo`
     - Native camera lifecycle, capture and device information.
   * - :doc:`BswLib`
     - Frame leases, reference counts and resource metrics.
   * - :doc:`EbOs`
     - Mutexes and task delays.
   * - :doc:`LocalTime`
     - Monotonic deadlines and timing.
   * - :doc:`NeoContracts`
     - Profiles, frames, states and statistics.
   * - ESP-IDF / FreeRTOS
     - Producer task and backend resource samples.

**Source files**

`CamPipe.h <https://github.com/NeoTech-vietnam/CamPipe/blob/f0fb17c375ce171536473147a76a9999643df4a3/CamPipe.h>`__, `CamPipe.c <https://github.com/NeoTech-vietnam/CamPipe/blob/f0fb17c375ce171536473147a76a9999643df4a3/CamPipe.c>`__, `CamPipe_Backend.h <https://github.com/NeoTech-vietnam/CamPipe/blob/f0fb17c375ce171536473147a76a9999643df4a3/CamPipe_Backend.h>`__, `CamPipe_EspIdf.c <https://github.com/NeoTech-vietnam/CamPipe/blob/f0fb17c375ce171536473147a76a9999643df4a3/CamPipe_EspIdf.c>`__, `module.cmake <https://github.com/NeoTech-vietnam/CamPipe/blob/f0fb17c375ce171536473147a76a9999643df4a3/module.cmake>`__.

6 Requirements traceability
---------------------------

.. list-table:: Requirements traceability
   :header-rows: 1

   * - Requirement
     - Description
     - Satisfied by
     - Verification evidence
   * - ``NEOCAM-SWS-CamPipe-001``
     - Publish a single latest frame and acquire only newer sequences.
     - :ref:`Latest-frame publication <sws-campipe-publication>`
     - ``cam_pipe`` host case in ``test/test_cam_pipe.c``.
   * - ``NEOCAM-SWS-CamPipe-002``
     - Run one operation at a time and restore preview after a photo.
     - :ref:`Profile change and still capture <sws-campipe-transition>`
     - ``cam_pipe`` host case checks profile changes, capture and lease behavior.
   * - ``NEOCAM-SWS-CamPipe-003``
     - Preserve resources while a shutdown is incomplete.
     - :ref:`Producer shutdown <sws-campipe-stop>`
     - `CamPipe.c <https://github.com/NeoTech-vietnam/CamPipe/blob/f0fb17c375ce171536473147a76a9999643df4a3/CamPipe.c>`__, `CamPipe_EspIdf.c <https://github.com/NeoTech-vietnam/CamPipe/blob/f0fb17c375ce171536473147a76a9999643df4a3/CamPipe_EspIdf.c>`__ and ``cam_pipe`` host case.

7 Functional specification
--------------------------

.. _sws-campipe-publication:

Latest-frame publication
~~~~~~~~~~~~~~~~~~~~~~~~

The producer takes a native JPEG via CamIo, publishes a copied frame, and releases the preceding publisher reference. A reader receives its own reference only when the latest sequence exceeds its cursor. Acquisition during a transition returns busy. Duplicate native timestamps and acquisition failures do not produce a new publication.

.. _sws-campipe-transition:

Profile change and still capture
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

On profile or photo requests, the producer drops its latest reference and drains external preview leases before reconfiguring. It warms the selected profile before continuing. For photo and for failed profile changes after reconfiguration, it attempts to restore the preceding stable preview profile. A photo is handed off only once successful completion and restoration are confirmed.

.. _sws-campipe-stop:

Producer shutdown
~~~~~~~~~~~~~~~~~

Stop marks the pipeline as stopping, waits for the backend producer to quiesce, then checks the waiting-client count before deleting the mutex. External leases remain governed by the pool. If a stop call times out or reports busy, the owner can retry.

Error classification
~~~~~~~~~~~~~~~~~~~~

Bad output pointers and invalid profiles report ``NEO_E_PARAM``. A stopped or unavailable pipeline may report ``NEO_E_NOT_READY``. Operation overlap returns ``NEO_E_BUSY`` and expired waits return ``NEO_E_TIMEOUT``. Capture and restoration errors are recorded separately in statistics. A restoration failure puts the producer into error state.

8 API specification
-------------------

Imported types
~~~~~~~~~~~~~~

The service signatures use :doc:`NeoContracts` for frame, profile, statistics and camera-information definitions.

Service definitions
~~~~~~~~~~~~~~~~~~~

.. list-table:: CamPipe_Start
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``CamPipe_Start``
   * - Syntax
     - ``Neo_StatusType CamPipe_Start(void)``
   * - Execution and reentrancy
     - Synchronous startup. Starts a producer that activates the default profile asynchronously. Lifecycle owner only.
   * - Parameters (in)
     - None.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - None.
   * - Return value
     - ``NEO_OK``, ``NEO_E_STATE`` May propagate camera, mutex or backend startup errors.
   * - Description
     - Requires the camera to provide information and the pool to be initialized.
   * - Available via
     - ``CamPipe.h``

.. list-table:: CamPipe_Stop
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``CamPipe_Stop``
   * - Syntax
     - ``Neo_StatusType CamPipe_Stop(void)``
   * - Execution and reentrancy
     - Synchronous. The composition owner serializes lifecycle calls.
   * - Parameters (in)
     - None.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - None.
   * - Return value
     - ``NEO_OK``, ``NEO_E_BUSY``, ``NEO_E_TIMEOUT``
   * - Description
     - Requests stop and waits for the producer. Retains stopping state if teardown must be retried.
   * - Available via
     - ``CamPipe.h``

.. list-table:: CamPipe_AcquireLatest
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``CamPipe_AcquireLatest``
   * - Syntax
     - ``Neo_StatusType CamPipe_AcquireLatest(uint64 after_seq, uint32 timeout_ms, Neo_FrameType *frame)``
   * - Execution and reentrancy
     - Synchronous. Concurrent calls are supported while the pipeline is active, with lifecycle serialized by the composition owner.
   * - Parameters (in)
     - ``after_seq`` exclusive sequence lower bound, ``timeout_ms`` wait limit.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - ``frame`` retained on success.
   * - Return value
     - ``NEO_OK``, ``NEO_E_PARAM``, ``NEO_E_NOT_READY``, ``NEO_E_BUSY``, ``NEO_E_TIMEOUT`` May report the stored pipeline error or a retain error.
   * - Description
     - Waits for a strictly newer publication while running. A zero timeout performs a single attempt.
   * - Available via
     - ``CamPipe.h``

.. list-table:: CamPipe_Photo
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``CamPipe_Photo``
   * - Syntax
     - ``Neo_StatusType CamPipe_Photo(Neo_FrameType *frame)``
   * - Execution and reentrancy
     - Synchronous wait on the producer. Only one photo or profile command may execute at a time.
   * - Parameters (in)
     - None.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - ``frame`` the retained image on success.
   * - Return value
     - ``NEO_OK``, ``NEO_E_PARAM``, ``NEO_E_NOT_READY``, ``NEO_E_BUSY``, ``NEO_E_STATE``, ``NEO_E_TIMEOUT`` May propagate capture or restoration errors.
   * - Description
     - Acquires a full-resolution JPEG and restores preview before returning success.
   * - Available via
     - ``CamPipe.h``

.. list-table:: CamPipe_RequestProfile
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``CamPipe_RequestProfile``
   * - Syntax
     - ``Neo_StatusType CamPipe_RequestProfile(Neo_ProfileIdType profile)``
   * - Execution and reentrancy
     - Asynchronous profile change. Admission is serialized with photo and other profile commands.
   * - Parameters (in)
     - ``profile`` preview preset.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - None.
   * - Return value
     - ``NEO_OK``, ``NEO_E_PARAM``, ``NEO_E_NOT_READY``, ``NEO_E_BUSY``
   * - Description
     - Returns acceptance. Read statistics for progress and outcome.
   * - Available via
     - ``CamPipe.h``

.. list-table:: CamPipe_GetStats
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``CamPipe_GetStats``
   * - Syntax
     - ``Neo_StatusType CamPipe_GetStats(Neo_PipelineStatsType *stats)``
   * - Execution and reentrancy
     - Synchronous. Concurrent calls are supported while the pipeline is active, with lifecycle serialized by the composition owner.
   * - Parameters (in)
     - None.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - ``stats`` pipeline snapshot and sampled resource statistics.
   * - Return value
     - ``NEO_OK``, ``NEO_E_PARAM``
   * - Description
     - Reads counters and recent p95 timing values.
   * - Available via
     - ``CamPipe.h``

.. list-table:: CamPipe_GetInfo
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``CamPipe_GetInfo``
   * - Syntax
     - ``Neo_StatusType CamPipe_GetInfo(Neo_CameraInfoType *info)``
   * - Execution and reentrancy
     - Synchronous. Concurrent calls are supported while the pipeline is active, with lifecycle serialized by the composition owner.
   * - Parameters (in)
     - None.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - ``info`` camera details on success.
   * - Return value
     - The result of ``CamIo_GetInfo``.
   * - Description
     - Delegates to the camera adapter.
   * - Available via
     - ``CamPipe.h``

.. list-table:: CamPipe_Release
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``CamPipe_Release``
   * - Syntax
     - ``Neo_StatusType CamPipe_Release(Neo_BufferTokenType token)``
   * - Execution and reentrancy
     - Synchronous. Concurrent calls are supported while the pipeline is active, with lifecycle serialized by the composition owner.
   * - Parameters (in)
     - ``token`` one outstanding lease.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - None.
   * - Return value
     - The result of ``MediaBuf_Release``.
   * - Description
     - Returns one reference to the pool.
   * - Available via
     - ``CamPipe.h``

9 Sequence diagrams
-------------------

:ref:`The product sequence diagrams <neocam-runtime-sequences>` show the end-to-end interactions. The producer handles the following photo sequence.

#. Accept the command and stop serving the previous latest frame.
#. Wait for preview leases to drain, activate the photo profile, and warm up the camera.
#. Capture the still into the dedicated photo pool slot.
#. Restore and warm the previous preview profile, then transfer the photo lease to the waiting caller if it is still eligible.

10 Configuration specification
------------------------------

.. list-table:: Profile, timing and worker settings
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Owner
     - ``Conf/CamPipe/CamPipe_Cfg.h``
   * - Type
     - C preprocessor constants
   * - Default
     - ``NEO_PROFILE_SAFE``, operation 10000 ms, warm-up 2000 ms / 3 frames, 64 timing samples, 8192-byte stack, priority 5, core -1 (unpinned).
   * - Units or allowed values
     - Deadlines in milliseconds, stack in bytes, positive frame/sample counts, affinity -1, 0 or 1.
   * - Effective
     - At firmware build time.

.. list-table:: Product profile presets
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Owner
     - ``GConf/CameraProfiles/Neo_Profiles.c``
   * - Type
     - ``Neo_ProfileType`` table
   * - Default
     - Safe 640×480/q12/30 FPS, smooth 640×480/q16/30 FPS, balanced 1280×720/q12/30 FPS, detail 1600×1200/q10/10 FPS, photo 2048×1536/q8/0 FPS.
   * - Units or allowed values
     - JPEG quality 0–63, image dimensions in pixels, and preview FPS targets. Every performance-qualified flag defaults to false.
   * - Effective
     - Compiled into the firmware. The selected entry applies when the producer activates the profile.
