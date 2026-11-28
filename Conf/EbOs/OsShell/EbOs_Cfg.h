/*<NeoTechHead>
 *************************************************************************
 *                              NeoTech
 *************************************************************************
 *
 * /   / /////  ///  ///// /////  ///  /   /
 * //  / /     /   /   /   /     /   / /   /
 * / / / ///   /   /   /   ///   /     /////
 * /  // /     /   /   /   /     /   / /   /
 * /   / /////  ///    /   /////  ///  /   /
 *
 *************************************************************************
 * Administrative Information
 *************************************************************************
 *
 * $Filename__:EbOs_Cfg.h$
 *
 * $Author____:Nguyen Ba Vu Thach$
 *
 * $Function__:NeoCam-specific policy for the EbOs native-task adapter.$
 *
 *************************************************************************
 * $Domain____:NeoTech$
 * $User______:Nguyen Ba Vu Thach$
 * $Date______:28.11.2026$
 * $Class_____:EbOs$
 * $Name______:EbOs_Cfg$
 * $Variant___:1.0.0$
 * $Revision__:2$
 * $Type______:H$
 * $State_____:PROTOTYPE$
 *
 *************************************************************************
 * List Of Changes
 *
 * $History
 *
 * 1.0.0; 1     28.11.2026 Nguyen Ba Vu Thach
 *   Add project-owned camera task policy and runnable wiring.
 * 1.0.0; 2     28.11.2026 Nguyen Ba Vu Thach
 *   Apply NeoTech source format and explicit integration requirements.
 *
 * $
 *
 *************************************************************************
</NeoTechHead>*/

#ifndef EBOS_CFG_H
#define EBOS_CFG_H

/*
 **********************************************************************************************************************
 * Includes
 **********************************************************************************************************************
 */


/*
 **********************************************************************************************************************
 * Defines / Macros
 **********************************************************************************************************************
 */

/** @brief   TRACE[NEO_EBOS_CFG_00001]
 *  @details The integration project selects the camera task stack in bytes.
 *           This is native-task policy, not an AUTOSAR conformance setting.
 */
#define EBOS_CAMERA_STACK_BYTES 8192U

/** @brief   TRACE[NEO_EBOS_CFG_00001]
 *  @details Camera task priority on the ESP-IDF FreeRTOS priority scale.
 */
#define EBOS_CAMERA_PRIORITY 5U

/** @brief   TRACE[NEO_EBOS_CFG_00001]
 *  @details Preserve the build-time producer affinity override. Minus one
 *           leaves the task unpinned; zero and one select an ESP32-S3 core.
 */
#ifndef NEOCAM_PRODUCER_CORE
#define NEOCAM_PRODUCER_CORE (-1)
#endif

_Static_assert(NEOCAM_PRODUCER_CORE >= -1 && NEOCAM_PRODUCER_CORE <= 1,
               "Producer affinity must be unpinned, core 0, or core 1");

/*
 **********************************************************************************************************************
 * Types
 **********************************************************************************************************************
 */


/*
 **********************************************************************************************************************
 * Extern declarations
 **********************************************************************************************************************
 */


/*
 **********************************************************************************************************************
 * Function prototypes
 **********************************************************************************************************************
 */

#endif /* EBOS_CFG_H */
