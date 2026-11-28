cmake_minimum_required(VERSION 3.16)
if(CMAKE_HOST_WIN32)
    # Deep workspaces can exceed CreateProcess's compiler command-line limit.
    set(CMAKE_NINJA_FORCE_RESPONSE_FILE ON)
endif()
set(EXTRA_COMPONENT_DIRS "${CMAKE_CURRENT_LIST_DIR}/TOOLCONF/esp-idf/BSW"
                         "${CMAKE_CURRENT_LIST_DIR}/TOOLCONF/esp-idf/Rte"
                         "${CMAKE_CURRENT_LIST_DIR}/TOOLCONF/esp-idf/ApplicationLayer"
                         "${CMAKE_CURRENT_LIST_DIR}/TOOLCONF/esp-idf/main")
include($ENV{IDF_PATH}/tools/cmake/project.cmake)
if(NOT IDF_VERSION_MAJOR EQUAL 6 OR NOT IDF_VERSION_MINOR EQUAL 0 OR NOT IDF_VERSION_PATCH EQUAL 1)
    message(FATAL_ERROR "NeoCam requires ESP-IDF 6.0.1")
endif()
project(neocam_csw)
