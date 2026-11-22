.. _sws-neocontracts:

Specification of NeoContracts
=============================

.. list-table:: Document metadata
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Document ID
     - ``NEOCAM-SWS-NeoContracts``
   * - Owner
     - NeoCam integration
   * - Status
     - Reference for the selected NeoCam release
   * - Selected ref
     - ``neocontracts/1.0.0@neotech/prototype``
   * - Source commit
     - `79de8ffd201dbb3a8f2295b8545e96e85deaa7d2 <https://github.com/NeoTech-vietnam/NeoContracts/tree/79de8ffd201dbb3a8f2295b8545e96e85deaa7d2>`__

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

NeoContracts owns the project-level types and typed port tables shared between NeoCam modules. The integration repository provides the profile lookup definitions and preset data.

2 Acronyms and abbreviations
----------------------------

.. list-table:: Terminology
   :header-rows: 1

   * - Term
     - Meaning
   * - Contract
     - Shared C data or callback shape between modules.
   * - FPS
     - Frames per second.
   * - Profile epoch
     - Identifier of a camera profile activation.

3 Related documentation
-----------------------

* :doc:`NeoCam architecture and adaptation profile <../architecture/architecture>`
* :doc:`../operations/runtime`
* :doc:`../validation/optimization`

4 Constraints and assumptions
-----------------------------

* Consumers may read a JPEG through its frame descriptor only until the corresponding lease is released.
* The profile count is a table bound. Preview selection excludes the photo preset.
* The shared types use CUCEL standard types and carry no ESP-IDF handles.

5 Dependencies and file structure
---------------------------------

.. list-table:: Dependencies
   :header-rows: 1

   * - Dependency
     - Purpose
   * - :doc:`CUCEL`
     - Supplies Platform_Types.h and Std_Types.h through the standard types header.
   * - ``GConf/CameraProfiles/Neo_Profiles.c``
     - Provides immutable profile data and implements the declared lookup functions.

**Source files**

`Neo_Types.h <https://github.com/NeoTech-vietnam/NeoContracts/blob/79de8ffd201dbb3a8f2295b8545e96e85deaa7d2/Neo_Types.h>`__, `Neo_CameraTypes.h <https://github.com/NeoTech-vietnam/NeoContracts/blob/79de8ffd201dbb3a8f2295b8545e96e85deaa7d2/Neo_CameraTypes.h>`__, `Neo_HttpTypes.h <https://github.com/NeoTech-vietnam/NeoContracts/blob/79de8ffd201dbb3a8f2295b8545e96e85deaa7d2/Neo_HttpTypes.h>`__, `module.cmake <https://github.com/NeoTech-vietnam/NeoContracts/blob/79de8ffd201dbb3a8f2295b8545e96e85deaa7d2/module.cmake>`__.

6 Requirements traceability
---------------------------

.. list-table:: Requirements traceability
   :header-rows: 1

   * - Requirement
     - Description
     - Satisfied by
     - Verification evidence
   * - ``NEOCAM-SWS-NeoContracts-001``
     - Carry frame payload metadata and a release token through module boundaries.
     - :ref:`Shared frame and lease contract <sws-neocontracts-frame>`
     - `Neo_Types.h <https://github.com/NeoTech-vietnam/NeoContracts/blob/79de8ffd201dbb3a8f2295b8545e96e85deaa7d2/Neo_Types.h>`__, `Neo_HttpTypes.h <https://github.com/NeoTech-vietnam/NeoContracts/blob/79de8ffd201dbb3a8f2295b8545e96e85deaa7d2/Neo_HttpTypes.h>`__ and the ``camera_buffers`` and ``application`` host cases.
   * - ``NEOCAM-SWS-NeoContracts-002``
     - Expose a common immutable view of presets.
     - :ref:`Product profile lookup <sws-neocontracts-profiles>`
     - ``GConf/CameraProfiles/Neo_Profiles.c`` and ``test/test_application.c``.

7 Functional specification
--------------------------

.. _sws-neocontracts-frame:

Shared frame and lease contract
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The frame carries payload pointer, byte count, dimensions, capture and copy timing, source timestamp, pool token, sequence, profile epoch, and target cadence. The token combines slot index and generation. Ownership remains governed by the producing service.

.. _sws-neocontracts-profiles:

Product profile lookup
~~~~~~~~~~~~~~~~~~~~~~

Profile lookup returns a pointer to the corresponding product entry by ID or exact name for the lifetime of the firmware. Missing names, null names and out-of-range IDs return a null pointer.

Error classification
~~~~~~~~~~~~~~~~~~~~

The status enum describes errors produced by the owning module. The profile lookup functions signal a missing selection with ``NULL_PTR``.

8 API specification
-------------------

Base types
~~~~~~~~~~

.. list-table:: Neo_StatusType
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Name
     - ``Neo_StatusType``
   * - Kind
     - Enumeration
   * - Representation / range
     - Ordinal values 0–8 in declaration order.
   * - Description
     - Result codes: ``NEO_OK``, ``NEO_E_PARAM``, ``NEO_E_STATE``, ``NEO_E_BUSY``, ``NEO_E_MEMORY``, ``NEO_E_IO``, ``NEO_E_TIMEOUT``, ``NEO_E_TOO_LARGE``, ``NEO_E_NOT_READY``.
   * - Available via
     - ``Neo_Types.h``

.. list-table:: Neo_BufferTokenType
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Name
     - ``Neo_BufferTokenType``
   * - Kind
     - Structure
   * - Representation / range
     - ``uint16 slot`` and ``uint32 generation``.
   * - Description
     - Identity of a pool lease.
   * - Available via
     - ``Neo_Types.h``

.. list-table:: Neo_FrameType
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Name
     - ``Neo_FrameType``
   * - Kind
     - Structure
   * - Representation / range
     - Pointer to constant bytes, length in bytes, pixel dimensions, timing, token, sequence, profile epoch and cadence.
   * - Description
     - Description of a leased JPEG. Capture duration is in milliseconds and acquisition/copy durations and timestamp are in microseconds.
   * - Available via
     - ``Neo_Types.h``

.. list-table:: Neo_CameraInfoType
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Name
     - ``Neo_CameraInfoType``
   * - Kind
     - Structure
   * - Representation / range
     - ``uint16`` pixel dimensions and sensor PID, ``char sensor_name[16]``.
   * - Description
     - Camera identification and active dimensions.
   * - Available via
     - ``Neo_Types.h``

Camera and HTTP types
~~~~~~~~~~~~~~~~~~~~~

.. list-table:: Neo_ProfileIdType
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Name
     - ``Neo_ProfileIdType``
   * - Kind
     - Enumeration
   * - Representation / range
     - Ordinal values starting at zero.
   * - Description
     - ``NEO_PROFILE_SAFE``, ``NEO_PROFILE_SMOOTH``, ``NEO_PROFILE_BALANCED``, ``NEO_PROFILE_DETAIL``, ``NEO_PROFILE_PHOTO``, ``NEO_PROFILE_COUNT``.
   * - Available via
     - ``Neo_CameraTypes.h``

.. list-table:: Neo_ProfileType
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Name
     - ``Neo_ProfileType``
   * - Kind
     - Structure
   * - Representation / range
     - ID, name, pixel dimensions, JPEG quality, target FPS and Boolean qualification flag.
   * - Description
     - Immutable preset entry from the integration table.
   * - Available via
     - ``Neo_CameraTypes.h``

.. list-table:: Neo_PipeStateType
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Name
     - ``Neo_PipeStateType``
   * - Kind
     - Enumeration
   * - Representation / range
     - Ordinal values starting at zero.
   * - Description
     - ``NEO_PIPE_STOPPED``, ``NEO_PIPE_RUNNING``, ``NEO_PIPE_SWITCHING``, ``NEO_PIPE_PHOTO``, ``NEO_PIPE_ERROR``, ``NEO_PIPE_STOPPING``.
   * - Available via
     - ``Neo_CameraTypes.h``

.. list-table:: Neo_PipelineStatsType
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Name
     - ``Neo_PipelineStatsType``
   * - Kind
     - Structure
   * - Representation / range
     - State, requested/active profile, epoch, frame counters, timing, JPEG sizes, free memory, task stack, build/network settings and last errors.
   * - Description
     - For the full field inventory see `Neo_CameraTypes.h <https://github.com/NeoTech-vietnam/NeoContracts/blob/79de8ffd201dbb3a8f2295b8545e96e85deaa7d2/Neo_CameraTypes.h>`__. Cadence is represented by ``capture_fps_x100`` and durations with a ``_us`` suffix are in microseconds.
   * - Available via
     - ``Neo_CameraTypes.h``

.. list-table:: Neo_HttpPortsType
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Name
     - ``Neo_HttpPortsType``
   * - Kind
     - Function-pointer structure
   * - Representation / range
     - ``page``, ``metrics``, ``frame``, ``stream_next``, ``photo``, ``profile``, ``select_profile``, ``release``, ``stream_opened``, ``stream_frame``.
   * - Description
     - Typed callbacks for content, capture, frame delivery, profile selection, lease release and stream diagnostics.
   * - Available via
     - ``Neo_HttpTypes.h``

Profile lookup services
~~~~~~~~~~~~~~~~~~~~~~~

.. list-table:: Neo_ProfileGet
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``Neo_ProfileGet``
   * - Syntax
     - ``const Neo_ProfileType *Neo_ProfileGet(Neo_ProfileIdType id)``
   * - Execution and reentrancy
     - Synchronous. Returns a borrowed pointer into an immutable product table.
   * - Parameters (in)
     - ``id`` profile identifier.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - None.
   * - Return value
     - Profile pointer, or ``NULL_PTR`` if out of range.
   * - Description
     - Returns a preset by ID.
   * - Available via
     - ``Neo_CameraTypes.h``

.. list-table:: Neo_ProfileFind
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``Neo_ProfileFind``
   * - Syntax
     - ``const Neo_ProfileType *Neo_ProfileFind(const char *name)``
   * - Execution and reentrancy
     - Synchronous. Returns a borrowed pointer into an immutable product table.
   * - Parameters (in)
     - ``name`` NUL-terminated exact profile name.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - None.
   * - Return value
     - Profile pointer, or ``NULL_PTR`` for null or unmatched names.
   * - Description
     - Finds a preset by its case-sensitive name.
   * - Available via
     - ``Neo_CameraTypes.h``

9 Sequence diagrams
-------------------

Not applicable. Port call sequences are specified in their owning modules and in :doc:`../architecture/architecture`.

10 Configuration specification
------------------------------

.. list-table:: Profile and benchmark values
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Owner
     - ``GConf/CameraProfiles/Neo_Profiles.c``
   * - Type
     - ``Neo_ProfileType`` constant table and C benchmark overrides
   * - Default
     - Five named presets. Global JPEG-quality override -1 (use each preset). Smooth target 30 FPS.
   * - Units or allowed values
     - The JPEG override accepts -1 or 0–63. Full product preset values are in :doc:`CamPipe`.
   * - Effective
     - At firmware build time.
