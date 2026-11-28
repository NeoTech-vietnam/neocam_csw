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
 * $Filename__:Os_Cfg.h$
 *
 * $Author____:Nguyen Ba Vu Thach$
 *
 * $Function__:NeoCam-owned basic-task selection and explicit bring-up check.$
 *
 *************************************************************************
 * $Domain____:NeoTech$
 * $User______:Nguyen Ba Vu Thach$
 * $Date______:28.11.2026$
 * $Class_____:EbOs$
 * $Name_____:Os_Cfg$
 * $Variant___:1.1.0$
 * $Revision__:1$
 * $Type_____:H$
 * $State_____:DRAFT$
 *
 *************************************************************************
 * List Of Changes
 *
 * $History
 *
 * 1.1.0; 1     28.11.2026 Nguyen Ba Vu Thach
 *   Add the explicitly limited ESP-IDF basic-task runtime profile.
 *
 * $
 *
 *************************************************************************
</NeoTechHead>*/

#ifndef OS_CFG_H
#define OS_CFG_H

/*
 **********************************************************************************************************************
 * Includes
 **********************************************************************************************************************
 */

#include "EbOs_Os.h"

/*
 **********************************************************************************************************************
 * Defines / Macros
 **********************************************************************************************************************
 */

/** @brief   TRACE[NEO_EBOS_OS_RUNTIME]
 *  @details Project table index for the on-demand task-service bring-up check.
 *           This task is dormant until explicitly activated by the project/test.
 */
#define Os_Task_ProjectCheck ((TaskType)0U)

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

/** @brief   TRACE[NEO_EBOS_OS_RUNTIME]
 *  @details Project policy; no product names or values are compiled into EbOs.
 */
extern const EbOs_OsConfigType Os_Config;

/*
 **********************************************************************************************************************
 * Function prototypes
 **********************************************************************************************************************
 */

/** @brief   TRACE[NEO_EBOS_OS_RUNTIME]
 *  @details Read the most recent explicit project-check result. The initial value
 *           is E_OS_STATE; E_OK means its identity, state and scheduling checks
 *           passed. This is a project diagnostic, not a standard OS service.
 *  @return  Last check result.
 */
StatusType Os_ProjectCheckResult(void);

#endif /* OS_CFG_H */
