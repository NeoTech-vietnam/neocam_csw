set(NEO_MODULE_SOURCES)
set(NEO_MODULE_INCLUDES)
include("${PROJECT_DIR}/CUCEL/module.cmake")
include("${PROJECT_DIR}/NeoContracts/module.cmake")
include("${PROJECT_DIR}/BootCtrl/module.cmake")
include("${PROJECT_DIR}/BswLib/module.cmake")
include("${PROJECT_DIR}/EbOs/module.cmake")
include("${PROJECT_DIR}/LocalTime/module.cmake")
include("${PROJECT_DIR}/CamIo/module.cmake")
include("${PROJECT_DIR}/CamPipe/module.cmake")
include("${PROJECT_DIR}/WifiStack/module.cmake")
include("${PROJECT_DIR}/HttpSrv/module.cmake")
idf_component_register(
    SRCS ${NEO_MODULE_SOURCES}
        "${PROJECT_DIR}/Conf/CamIo/CamIo_Cfg.c"
        "${PROJECT_DIR}/Conf/WifiStack/WifiMgr_Cfg.c"
        "${PROJECT_DIR}/Conf/HttpSrv/HttpSrv_Cfg.c"
        "${PROJECT_DIR}/GConf/CameraProfiles/Neo_Profiles.c"
    INCLUDE_DIRS ${NEO_MODULE_INCLUDES}
    "${PROJECT_DIR}/Conf/__CONFIG"
    "${PROJECT_DIR}/Conf/CUCEL"
    "${PROJECT_DIR}/Conf/CamIo"
    "${PROJECT_DIR}/Conf/CamPipe"
    "${PROJECT_DIR}/Conf/BswLib"
    "${PROJECT_DIR}/Conf/WifiStack"
    "${PROJECT_DIR}/Conf/HttpSrv"
    PRIV_REQUIRES esp_event esp_http_server esp_netif esp_psram esp_timer esp_wifi
                  nvs_flash freertos heap espressif__esp32-camera
)
# These overrides are benchmark builds; default presets remain hand-written C.
set(NEOCAM_BENCH_JPEG_QUALITY -1 CACHE STRING "JPEG quality override for controlled experiments")
set(NEOCAM_BENCH_SMOOTH_FPS 30 CACHE STRING "Smooth preset FPS cap (30 or experimental 60)")
set(NEOCAM_PRODUCER_CORE -1 CACHE STRING "Producer affinity: -1, 0, 1")
set(NEOCAM_WIFI_CHANNEL 1 CACHE STRING "SoftAP benchmark channel")
set(NEOCAM_WIFI_BANDWIDTH 20 CACHE STRING "Configured SoftAP bandwidth (20 or 40 MHz)")
if(NOT NEOCAM_BENCH_JPEG_QUALITY MATCHES "^(-1|[0-9]+)$" OR
   NEOCAM_BENCH_JPEG_QUALITY LESS -1 OR NEOCAM_BENCH_JPEG_QUALITY GREATER 63)
    message(FATAL_ERROR "NEOCAM_BENCH_JPEG_QUALITY must be -1 or 0..63")
endif()
if(NOT NEOCAM_BENCH_SMOOTH_FPS MATCHES "^(30|60)$")
    message(FATAL_ERROR "Smooth benchmark FPS must be 30 or 60")
endif()
if(NOT NEOCAM_PRODUCER_CORE MATCHES "^(-1|0|1)$")
    message(FATAL_ERROR "Invalid producer core")
endif()
if(NOT NEOCAM_WIFI_CHANNEL MATCHES "^[0-9]+$" OR
   NEOCAM_WIFI_CHANNEL LESS 1 OR NEOCAM_WIFI_CHANNEL GREATER 11)
    message(FATAL_ERROR "SoftAP channel must be 1..11")
endif()
if(NOT NEOCAM_WIFI_BANDWIDTH MATCHES "^(20|40)$")
    message(FATAL_ERROR "SoftAP bandwidth must be 20 or 40")
endif()
target_compile_definitions(${COMPONENT_LIB} PRIVATE
    NEOCAM_BENCH_JPEG_QUALITY=${NEOCAM_BENCH_JPEG_QUALITY}
    NEOCAM_BENCH_SMOOTH_FPS=${NEOCAM_BENCH_SMOOTH_FPS}
    NEOCAM_PRODUCER_CORE=${NEOCAM_PRODUCER_CORE}
    NEOCAM_WIFI_CHANNEL=${NEOCAM_WIFI_CHANNEL}
    NEOCAM_WIFI_BANDWIDTH=${NEOCAM_WIFI_BANDWIDTH})
