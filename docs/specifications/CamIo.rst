.. _sws-camio:

Specification of CamIo
======================

.. list-table:: Document metadata
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Document ID
     - ``NEOCAM-SWS-CamIo``
   * - Owner
     - NeoCam integration
   * - Status
     - Reference for the selected NeoCam release
   * - Selected ref
     - ``camio/1.0.0@neotech/prototype``
   * - Source commit
     - `8d62a4fec49fbb1132e1ce085a205f6534307658 <https://github.com/NeoTech-vietnam/CamIo/tree/8d62a4fec49fbb1132e1ce085a205f6534307658>`__

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

CamIo owns the native camera adapter. It validates product wiring and profile parameters, serializes capture, and hands out copied JPEG leases.

2 Acronyms and abbreviations
----------------------------

.. list-table:: Terminology
   :header-rows: 1

   * - Term
     - Meaning
   * - SCCB
     - Serial Camera Control Bus, used for sensor control.
   * - DVP
     - Parallel camera data interface.
   * - XCLK
     - External clock supplied to the sensor.

3 Related documentation
-----------------------

* :doc:`NeoCam architecture and adaptation profile <../architecture/architecture>`
* :doc:`../operations/runtime`
* :doc:`../validation/validation`

4 Constraints and assumptions
-----------------------------

* Lifecycle operations are serialized by composition. CamPipe controls transitions during steady operation.
* A copied frame lease survives native reconfiguration. The client releases it exactly once.
* The backend expects a supported JPEG sensor and PSRAM.

5 Dependencies and file structure
---------------------------------

.. list-table:: Dependencies
   :header-rows: 1

   * - Dependency
     - Purpose
   * - :doc:`BswLib`
     - Supplies preview and photo slots.
   * - :doc:`EbOs`
     - Provides the camera operation mutex.
   * - :doc:`LocalTime`
     - Times native acquisition and copying.
   * - :doc:`NeoContracts`
     - Defines camera information, profiles and frame types.
   * - esp32-camera and ESP-IDF
     - Configure and drive the sensor, and return native framebuffers.

**Source files**

`CamIo.h <https://github.com/NeoTech-vietnam/CamIo/blob/8d62a4fec49fbb1132e1ce085a205f6534307658/CamIo.h>`__, `CamIo_ConfigTypes.h <https://github.com/NeoTech-vietnam/CamIo/blob/8d62a4fec49fbb1132e1ce085a205f6534307658/CamIo_ConfigTypes.h>`__, `CamIo.c <https://github.com/NeoTech-vietnam/CamIo/blob/8d62a4fec49fbb1132e1ce085a205f6534307658/CamIo.c>`__, `CamIo_Backend.h <https://github.com/NeoTech-vietnam/CamIo/blob/8d62a4fec49fbb1132e1ce085a205f6534307658/CamIo_Backend.h>`__, `CamIo_EspIdf.c <https://github.com/NeoTech-vietnam/CamIo/blob/8d62a4fec49fbb1132e1ce085a205f6534307658/CamIo_EspIdf.c>`__, `module.cmake <https://github.com/NeoTech-vietnam/CamIo/blob/8d62a4fec49fbb1132e1ce085a205f6534307658/module.cmake>`__.

6 Requirements traceability
---------------------------

.. list-table:: Requirements traceability
   :header-rows: 1

   * - Requirement
     - Description
     - Satisfied by
     - Verification evidence
   * - ``NEOCAM-SWS-CamIo-001``
     - Return the native frame and transfer only a copied lease.
     - :ref:`Native frame ownership <sws-camio-frame>`
     - ``camera_buffers`` host case in ``test/test_camera_buffers.c``.
   * - ``NEOCAM-SWS-CamIo-002``
     - Preserve copied leases while reconfiguring native ownership.
     - :ref:`Profile reconfiguration and teardown <sws-camio-mode>`
     - ``camera_buffers`` host case in ``test/test_camera_buffers.c``.

7 Functional specification
--------------------------

.. _sws-camio-frame:

Native frame ownership
~~~~~~~~~~~~~~~~~~~~~~

Capture reserves a pool slot, locks camera access, and acquires one backend frame. It checks JPEG format, dimensions, payload and capacity, copies the bytes on success, and returns every acquired native buffer. Failure releases the copied slot reference.

.. _sws-camio-mode:

Profile reconfiguration and teardown
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Start applies the safe profile. Profile changes stop and reinitialize the backend if necessary. A failed transition leaves capture unavailable until a valid configuration is reapplied. Deinitialization refuses a busy operation or outstanding pool leases.

Error classification
~~~~~~~~~~~~~~~~~~~~

Invalid wiring, profile or output arguments yield ``NEO_E_PARAM``. Busy transitions or teardown yield ``NEO_E_BUSY``. A missing or failed camera configuration can yield ``NEO_E_NOT_READY``. Backend acquisition failures and oversized images propagate with no lease transferred.

8 API specification
-------------------

.. list-table:: CamIo_ConfigType
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Name
     - ``CamIo_ConfigType``
   * - Kind
     - Structure
   * - Representation / range
     - Signed GPIO assignments, clock frequency, image dimensions, JPEG quality and native buffer count.
   * - Description
     - Board wiring and default native camera setup.
   * - Available via
     - ``CamIo_ConfigTypes.h``

.. list-table:: CamIo_Config
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Name
     - ``CamIo_Config``
   * - Kind
     - Product configuration object
   * - Description
     - Configuration supplied by the integration repository.
   * - Available via
     - ``CamIo_ConfigTypes.h``

.. list-table:: CamIo_ValidateConfig
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``CamIo_ValidateConfig``
   * - Syntax
     - ``Neo_StatusType CamIo_ValidateConfig(const CamIo_ConfigType *config)``
   * - Execution and reentrancy
     - Synchronous. Stateless for a stable input structure.
   * - Parameters (in)
     - ``config`` candidate camera configuration.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - None.
   * - Return value
     - ``NEO_OK``, ``NEO_E_PARAM``
   * - Description
     - Validates dimensions, quality, buffers, clock and GPIO constraints.
   * - Available via
     - ``CamIo_ConfigTypes.h``

.. list-table:: CamIo_Init
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``CamIo_Init``
   * - Syntax
     - ``Neo_StatusType CamIo_Init(void)``
   * - Execution and reentrancy
     - Synchronous. The composition owner serializes lifecycle calls after clients have quiesced.
   * - Parameters (in)
     - None.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - None.
   * - Return value
     - ``NEO_OK``, ``NEO_E_STATE``, ``NEO_E_PARAM`` May propagate backend or mutex failure.
   * - Description
     - Configures camera access and the safe preview profile.
   * - Available via
     - ``CamIo.h``

.. list-table:: CamIo_Deinit
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``CamIo_Deinit``
   * - Syntax
     - ``Neo_StatusType CamIo_Deinit(void)``
   * - Execution and reentrancy
     - Synchronous. The composition owner serializes lifecycle calls after clients have quiesced.
   * - Parameters (in)
     - None.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - None.
   * - Return value
     - ``NEO_OK``, ``NEO_E_BUSY`` May propagate backend failure.
   * - Description
     - Stops backend ownership and frees the mutex after success.
   * - Available via
     - ``CamIo.h``

.. list-table:: CamIo_SetProfile
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``CamIo_SetProfile``
   * - Syntax
     - ``Neo_StatusType CamIo_SetProfile(Neo_ProfileIdType profile)``
   * - Execution and reentrancy
     - Synchronous. The pipeline serializes transitions and the camera mutex guards operations.
   * - Parameters (in)
     - ``profile`` supported preset ID.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - None.
   * - Return value
     - ``NEO_OK``, ``NEO_E_PARAM``, ``NEO_E_NOT_READY``, ``NEO_E_BUSY`` May propagate backend failure.
   * - Description
     - Reconfigures the native camera for the selected preset.
   * - Available via
     - ``CamIo.h``

.. list-table:: CamIo_Capture
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``CamIo_Capture``
   * - Syntax
     - ``Neo_StatusType CamIo_Capture(Neo_FrameType *frame)``
   * - Execution and reentrancy
     - Synchronous. Camera operations are serialized internally with the camera mutex.
   * - Parameters (in)
     - None.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - ``frame`` populated with one transferred lease on success.
   * - Return value
     - ``NEO_OK``, ``NEO_E_PARAM``, ``NEO_E_NOT_READY``, ``NEO_E_BUSY``, ``NEO_E_TIMEOUT``, ``NEO_E_IO``, ``NEO_E_TOO_LARGE`` May propagate backend or pool errors.
   * - Description
     - Copies a native JPEG to a preview slot and returns the backend buffer before the call ends.
   * - Available via
     - ``CamIo.h``

.. list-table:: CamIo_CapturePhoto
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``CamIo_CapturePhoto``
   * - Syntax
     - ``Neo_StatusType CamIo_CapturePhoto(Neo_FrameType *frame)``
   * - Execution and reentrancy
     - Synchronous. Camera operations are serialized internally with the camera mutex.
   * - Parameters (in)
     - None.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - ``frame`` populated with one transferred lease on success.
   * - Return value
     - ``NEO_OK``, ``NEO_E_PARAM``, ``NEO_E_NOT_READY``, ``NEO_E_BUSY``, ``NEO_E_TIMEOUT``, ``NEO_E_IO``, ``NEO_E_TOO_LARGE`` May propagate backend or pool errors.
   * - Description
     - Copies a native JPEG to a photo slot and returns the backend buffer before the call ends.
   * - Available via
     - ``CamIo.h``

.. list-table:: CamIo_Release
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``CamIo_Release``
   * - Syntax
     - ``Neo_StatusType CamIo_Release(Neo_BufferTokenType token)``
   * - Execution and reentrancy
     - Synchronous. Uses the pool's concurrency contract.
   * - Parameters (in)
     - ``token`` valid lease.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - None.
   * - Return value
     - The result of ``MediaBuf_Release``.
   * - Description
     - Releases the copied frame reference.
   * - Available via
     - ``CamIo.h``

.. list-table:: CamIo_GetInfo
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``CamIo_GetInfo``
   * - Syntax
     - ``Neo_StatusType CamIo_GetInfo(Neo_CameraInfoType *info)``
   * - Execution and reentrancy
     - Synchronous. Camera operations are serialized internally with the camera mutex.
   * - Parameters (in)
     - None.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - ``info`` dimensions and sensor details when initialized.
   * - Return value
     - ``NEO_OK``, ``NEO_E_PARAM``, ``NEO_E_NOT_READY`` May propagate a lock error.
   * - Description
     - Returns the current camera information.
   * - Available via
     - ``CamIo.h``

9 Sequence diagrams
-------------------

#. CamPipe requests a capture and CamIo acquires a pool slot.
#. CamIo locks the backend, obtains a native frame and copies a valid JPEG.
#. CamIo returns the native frame before unlocking and returning the copied lease.

10 Configuration specification
------------------------------

.. list-table:: Board pin assignments
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Owner
     - ``Conf/CamIo/CamIo_Cfg.c``
   * - Type
     - ``CamIo_ConfigType`` GPIO fields
   * - Default
     - PWDN/reset -1, XCLK 10, SCCB SDA/SCL 40/39, D0–D7 15/17/18/16/14/12/11/48, VSYNC/HREF/PCLK 38/47/13.
   * - Units or allowed values
     - ESP32-S3 GPIO numbers. Optional PWDN/reset accept -1. Required pins are nonnegative and assignments cannot conflict.
   * - Effective
     - Compiled into the firmware and applied when the service starts.

.. list-table:: Native image setup
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Owner
     - ``Conf/CamIo/CamIo_Cfg.c``
   * - Type
     - ``CamIo_ConfigType`` image and clock fields
   * - Default
     - 20 MHz XCLK, 640×480 pixels, JPEG quality 12, two native buffers.
   * - Units or allowed values
     - Supported sizes 640×480, 1280×720, 1600×1200, 2048×1536. JPEG quality 0–63, buffer count 1–2. Active presets override size and quality.
   * - Effective
     - Compiled into the firmware and applied when the service starts.
