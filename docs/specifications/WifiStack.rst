.. _sws-wifistack:

Specification of WifiStack
==========================

.. list-table:: Document metadata
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Document ID
     - ``NEOCAM-SWS-WifiStack``
   * - Owner
     - NeoCam integration
   * - Status
     - Reference for the selected NeoCam release
   * - Selected ref
     - ``wifistack/1.0.0@neotech/prototype``
   * - Source commit
     - `364dfb24fdf8b44d763ac7142f0235d4f5919d39 <https://github.com/NeoTech-vietnam/WifiStack/tree/364dfb24fdf8b44d763ac7142f0235d4f5919d39>`__

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

WifiStack provides a local Wi-Fi access point. WifiMgr validates product settings and waits for readiness transitions. WifiIf owns the ESP-IDF network interface, driver and event registrations.

2 Acronyms and abbreviations
----------------------------

.. list-table:: Terminology
   :header-rows: 1

   * - Term
     - Meaning
   * - AP
     - Access point.
   * - SSID
     - Wireless network name.
   * - PSK
     - Pre-shared key.
   * - Netif
     - ESP-IDF network interface.

3 Related documentation
-----------------------

* :doc:`NeoCam architecture and adaptation profile <../architecture/architecture>`
* :doc:`../operations/runtime`
* :doc:`../validation/optimization`

4 Constraints and assumptions
-----------------------------

* The released implementation runs in SoftAP mode.
* BootCtrl serializes lifecycle operations. The readiness flag can be read concurrently.
* Read the native error from the serialized lifecycle context because its storage is not an atomic diagnostic channel.

5 Dependencies and file structure
---------------------------------

.. list-table:: Dependencies
   :header-rows: 1

   * - Dependency
     - Purpose
   * - :doc:`NeoContracts`
     - Defines shared status and platform types.
   * - :doc:`EbOs`
     - Delays readiness polls.
   * - :doc:`LocalTime`
     - Measures the readiness wait deadline.
   * - ESP-IDF esp_wifi, esp_netif, esp_event and C atomics
     - ESP-IDF networking backend.

**Source files**

`WifiMgr/WifiMgr.h <https://github.com/NeoTech-vietnam/WifiStack/blob/364dfb24fdf8b44d763ac7142f0235d4f5919d39/WifiMgr/WifiMgr.h>`__, `WifiMgr/WifiMgr_ConfigTypes.h <https://github.com/NeoTech-vietnam/WifiStack/blob/364dfb24fdf8b44d763ac7142f0235d4f5919d39/WifiMgr/WifiMgr_ConfigTypes.h>`__, `WifiMgr/WifiMgr_Config.c <https://github.com/NeoTech-vietnam/WifiStack/blob/364dfb24fdf8b44d763ac7142f0235d4f5919d39/WifiMgr/WifiMgr_Config.c>`__, `WifiMgr/WifiMgr.c <https://github.com/NeoTech-vietnam/WifiStack/blob/364dfb24fdf8b44d763ac7142f0235d4f5919d39/WifiMgr/WifiMgr.c>`__, `WifiIf/WifiIf.h <https://github.com/NeoTech-vietnam/WifiStack/blob/364dfb24fdf8b44d763ac7142f0235d4f5919d39/WifiIf/WifiIf.h>`__, `WifiIf/WifiIf_EspIdf.c <https://github.com/NeoTech-vietnam/WifiStack/blob/364dfb24fdf8b44d763ac7142f0235d4f5919d39/WifiIf/WifiIf_EspIdf.c>`__, `module.cmake <https://github.com/NeoTech-vietnam/WifiStack/blob/364dfb24fdf8b44d763ac7142f0235d4f5919d39/module.cmake>`__.

6 Requirements traceability
---------------------------

.. list-table:: Requirements traceability
   :header-rows: 1

   * - Requirement
     - Description
     - Satisfied by
     - Verification evidence
   * - ``NEOCAM-SWS-WifiStack-001``
     - Validate configuration and wait for event-driven AP state.
     - :ref:`WifiMgr validation and readiness <sws-wifistack-manager>`
     - `test/test_wifi_config.c <https://github.com/NeoTech-vietnam/WifiStack/blob/364dfb24fdf8b44d763ac7142f0235d4f5919d39/test/test_wifi_config.c>`__, `test/test_wifi_manager.c <https://github.com/NeoTech-vietnam/WifiStack/blob/364dfb24fdf8b44d763ac7142f0235d4f5919d39/test/test_wifi_manager.c>`__
   * - ``NEOCAM-SWS-WifiStack-002``
     - Manage AP resources and publish Wi-Fi event readiness.
     - :ref:`WifiIf ownership and events <sws-wifistack-adapter>`
     - `WifiIf/WifiIf_EspIdf.c <https://github.com/NeoTech-vietnam/WifiStack/blob/364dfb24fdf8b44d763ac7142f0235d4f5919d39/WifiIf/WifiIf_EspIdf.c>`__. Host tests use a fake WifiIf.

7 Functional specification
--------------------------

.. _sws-wifistack-manager:

WifiMgr validation and readiness
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

WifiMgr accepts a 1–32-byte SSID and an empty password or 8–63-byte passphrase. Channel and bandwidth are constrained to the product validator's ranges. Start and stop poll WifiIf readiness at 10 ms intervals up to the configured deadline. Failed start waiting triggers a best-effort stop.

.. _sws-wifistack-adapter:

WifiIf ownership and events
~~~~~~~~~~~~~~~~~~~~~~~~~~~

WifiIf creates or borrows the default event loop, registers an AP event handler and initializes the driver with RAM storage. AP start and stop events update the atomic ready flag. Cleanup acts on retained handles, while the shared ESP-IDF network stack initialization persists across restarts.

Error classification
~~~~~~~~~~~~~~~~~~~~

Validation returns ``NEO_E_PARAM`` for unsupported settings. Driver failures are logged and mapped to memory or I/O status. The first native failure is retained by WifiIf. The manager reports ``NEO_E_TIMEOUT`` if the requested readiness state does not arrive.

8 API specification
-------------------

WifiMgr interfaces
~~~~~~~~~~~~~~~~~~

.. list-table:: WifiMgr_ConfigType
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Name
     - ``WifiMgr_ConfigType``
   * - Kind
     - Structure
   * - Representation / range
     - SSID and password string pointers, ``uint8`` channel, max client count and bandwidth.
   * - Description
     - Active AP parameters.
   * - Available via
     - ``WifiMgr_ConfigTypes.h``

.. list-table:: WifiMgr_Config
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Name
     - ``WifiMgr_Config``
   * - Kind
     - Product configuration object
   * - Description
     - SoftAP settings compiled by the integration repository.
   * - Available via
     - ``WifiMgr_ConfigTypes.h``

.. list-table:: WifiMgr_ValidateConfig
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``WifiMgr_ValidateConfig``
   * - Syntax
     - ``Neo_StatusType WifiMgr_ValidateConfig(const WifiMgr_ConfigType *config)``
   * - Execution and reentrancy
     - Synchronous. Stateless for a stable input structure.
   * - Parameters (in)
     - ``config`` candidate settings.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - None.
   * - Return value
     - ``NEO_OK``, ``NEO_E_PARAM``
   * - Description
     - Checks lengths, channel, max client count and bandwidth.
   * - Available via
     - ``WifiMgr.h``

.. list-table:: WifiMgr_Init
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``WifiMgr_Init``
   * - Syntax
     - ``Neo_StatusType WifiMgr_Init(void)``
   * - Execution and reentrancy
     - Synchronous. The composition owner serializes lifecycle calls.
   * - Parameters (in)
     - None.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - None.
   * - Return value
     - ``NEO_OK``, validation result or WifiIf error.
   * - Description
     - Checks product settings and initializes WifiIf.
   * - Available via
     - ``WifiMgr.h``

.. list-table:: WifiMgr_Start
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``WifiMgr_Start``
   * - Syntax
     - ``Neo_StatusType WifiMgr_Start(void)``
   * - Execution and reentrancy
     - Synchronous. The composition owner serializes lifecycle calls.
   * - Parameters (in)
     - None.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - None.
   * - Return value
     - ``NEO_OK``, ``NEO_E_STATE``, ``NEO_E_TIMEOUT`` May propagate a WifiIf error.
   * - Description
     - Starts AP and waits for readiness.
   * - Available via
     - ``WifiMgr.h``

.. list-table:: WifiMgr_Stop
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``WifiMgr_Stop``
   * - Syntax
     - ``Neo_StatusType WifiMgr_Stop(void)``
   * - Execution and reentrancy
     - Synchronous. The composition owner serializes lifecycle calls.
   * - Parameters (in)
     - None.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - None.
   * - Return value
     - ``NEO_OK``, ``NEO_E_TIMEOUT`` May propagate a WifiIf error.
   * - Description
     - Stops AP and waits until it is no longer ready.
   * - Available via
     - ``WifiMgr.h``

.. list-table:: WifiMgr_Deinit
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``WifiMgr_Deinit``
   * - Syntax
     - ``Neo_StatusType WifiMgr_Deinit(void)``
   * - Execution and reentrancy
     - Synchronous. The composition owner serializes lifecycle calls.
   * - Parameters (in)
     - None.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - None.
   * - Return value
     - ``NEO_OK`` or the failed stop/deinitialization result.
   * - Description
     - Stops AP and releases WifiIf resources.
   * - Available via
     - ``WifiMgr.h``

.. list-table:: WifiMgr_IsReady
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``WifiMgr_IsReady``
   * - Syntax
     - ``boolean WifiMgr_IsReady(void)``
   * - Execution and reentrancy
     - Synchronous. Safe for concurrent readiness reads.
   * - Parameters (in)
     - None.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - None.
   * - Return value
     - Current AP readiness flag.
   * - Description
     - Reads WifiIf readiness.
   * - Available via
     - ``WifiMgr.h``

WifiIf interfaces
~~~~~~~~~~~~~~~~~

.. list-table:: WifiIf_Init
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``WifiIf_Init``
   * - Syntax
     - ``Neo_StatusType WifiIf_Init(const WifiMgr_ConfigType *config)``
   * - Execution and reentrancy
     - Synchronous. The composition owner serializes lifecycle calls.
   * - Parameters (in)
     - ``config`` validated AP settings.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - None.
   * - Return value
     - ``NEO_OK``, ``NEO_E_PARAM``, ``NEO_E_STATE`` ``NEO_E_IO``, ``NEO_E_MEMORY`` on backend failure.
   * - Description
     - Attaches the AP netif, registers events and applies native configuration.
   * - Available via
     - ``WifiIf.h``

.. list-table:: WifiIf_Start
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``WifiIf_Start``
   * - Syntax
     - ``Neo_StatusType WifiIf_Start(void)``
   * - Execution and reentrancy
     - Synchronous. The composition owner serializes lifecycle calls.
   * - Parameters (in)
     - None.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - None.
   * - Return value
     - ``NEO_OK``, ``NEO_E_STATE`` ``NEO_E_IO``, ``NEO_E_MEMORY`` on backend failure.
   * - Description
     - Requests native AP start. The event publishes readiness.
   * - Available via
     - ``WifiIf.h``

.. list-table:: WifiIf_Stop
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``WifiIf_Stop``
   * - Syntax
     - ``Neo_StatusType WifiIf_Stop(void)``
   * - Execution and reentrancy
     - Synchronous. The composition owner serializes lifecycle calls.
   * - Parameters (in)
     - None.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - None.
   * - Return value
     - ``NEO_OK`` ``NEO_E_IO``, ``NEO_E_MEMORY`` on backend failure.
   * - Description
     - Requests native AP stop. The event clears readiness.
   * - Available via
     - ``WifiIf.h``

.. list-table:: WifiIf_Deinit
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``WifiIf_Deinit``
   * - Syntax
     - ``Neo_StatusType WifiIf_Deinit(void)``
   * - Execution and reentrancy
     - Synchronous. The composition owner serializes lifecycle calls.
   * - Parameters (in)
     - None.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - None.
   * - Return value
     - ``NEO_OK`` ``NEO_E_IO``, ``NEO_E_MEMORY`` on backend failure.
   * - Description
     - Stops AP and cleans up owned native resources.
   * - Available via
     - ``WifiIf.h``

.. list-table:: WifiIf_IsReady
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``WifiIf_IsReady``
   * - Syntax
     - ``boolean WifiIf_IsReady(void)``
   * - Execution and reentrancy
     - Synchronous atomic read.
   * - Parameters (in)
     - None.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - None.
   * - Return value
     - True after the latest AP start event until stopped.
   * - Description
     - Reads the readiness flag.
   * - Available via
     - ``WifiIf.h``

.. list-table:: WifiIf_GetLastNativeError
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Service name
     - ``WifiIf_GetLastNativeError``
   * - Syntax
     - ``sint32 WifiIf_GetLastNativeError(void)``
   * - Execution and reentrancy
     - Synchronous. The composition owner serializes lifecycle calls.
   * - Parameters (in)
     - None.
   * - Parameters (inout)
     - None.
   * - Parameters (out)
     - None.
   * - Return value
     - ``sint32`` native error value, or zero.
   * - Description
     - Returns the first recorded native error in the current initialization attempt.
   * - Available via
     - ``WifiIf.h``

9 Sequence diagrams
-------------------

#. BootCtrl initializes WifiMgr, which validates settings and initializes WifiIf.
#. WifiMgr requests start. WifiIf callbacks set readiness after AP_START and the manager returns success on observing it.
#. On shutdown, WifiMgr requests stop, waits for AP_STOP readiness to clear, then deinitializes the owned resources.

10 Configuration specification
------------------------------

.. list-table:: SoftAP parameters
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Owner
     - ``Conf/WifiStack/WifiMgr_Cfg.c``
   * - Type
     - ``WifiMgr_ConfigType``
   * - Default
     - Product-configured SSID and passphrase, channel 1, client limit 2 and bandwidth 20 MHz.
   * - Units or allowed values
     - SSID 1–32 bytes, passphrase 8–63 bytes or empty for open AP, channel 1–11, 1–10 clients, 20 or 40 MHz.
   * - Effective
     - Compiled into firmware and read at WifiMgr_Init.

.. list-table:: Readiness timeout and network overrides
   :header-rows: 1
   :class: specification-fields

   * - Field
     - Value
   * - Owner
     - ``Conf/WifiStack/WifiMgr_Cfg.h``
   * - Type
     - C constants
   * - Default
     - 5000 ms, channel 1 and bandwidth 20 MHz.
   * - Units or allowed values
     - Milliseconds and compile-time channel/bandwidth overrides matching the validator.
   * - Effective
     - At firmware build time.
