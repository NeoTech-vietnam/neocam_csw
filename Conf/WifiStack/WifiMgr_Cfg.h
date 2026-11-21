#ifndef WIFIMGR_CFG_H
#define WIFIMGR_CFG_H
#include "WifiMgr_ConfigTypes.h"

#define WIFI_MGR_STATE_TIMEOUT_MS 5000U
#ifndef NEOCAM_WIFI_CHANNEL
#define NEOCAM_WIFI_CHANNEL 1
#endif
#ifndef NEOCAM_WIFI_BANDWIDTH
#define NEOCAM_WIFI_BANDWIDTH 20
#endif

_Static_assert(NEOCAM_WIFI_CHANNEL >= 1 && NEOCAM_WIFI_CHANNEL <= 11,
               "SoftAP benchmark channel must be 1..11");
_Static_assert(NEOCAM_WIFI_BANDWIDTH == 20 || NEOCAM_WIFI_BANDWIDTH == 40,
               "SoftAP bandwidth must be 20 or 40 MHz");

#endif
