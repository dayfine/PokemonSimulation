cmake_minimum_required(VERSION 3.20)
project(PinnedMapResourceSmoke NONE)

# Example:
# cmake -S integrations/arduino-source/resource-smoke -B build/map-resource-smoke \
#   -DCONSUMER_ROOT=/path/to/Arduino-Source -DPUBLISHER_SOURCE=/path/to/publishing-cache
if(NOT CONSUMER_ROOT OR NOT PUBLISHER_SOURCE)
    message(FATAL_ERROR "Set CONSUMER_ROOT and PUBLISHER_SOURCE to prepared consumer/cache directories.")
endif()
if(POKESIM_TOOLS_SOURCE)
    include("${POKESIM_TOOLS_SOURCE}/integrations/arduino-source/resource-maps.cmake")
else()
    include("${CMAKE_CURRENT_LIST_DIR}/../resource-maps.cmake")
endif()
foreach(GAME frlg bdsp)
    pa_pokesim_map_directory(MAPS "${GAME}" "${CONSUMER_ROOT}" "${PUBLISHER_SOURCE}")
    message(STATUS "Verified ${GAME}: ${MAPS}")
endforeach()
