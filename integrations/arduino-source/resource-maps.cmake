# Resolve a verified map-resource directory; never fetch or prepare during a build.
#
# include(/path/to/PokemonSimulation/integrations/arduino-source/resource-maps.cmake)
# pa_pokesim_map_directory(MAPS frlg /path/to/Arduino-Source /path/to/publishing-cache)
# Use MAPS in a resource loader, or pass a relative path to pa_embed_text_files().
# The caller must prepare the checked-in resource lock before configuring CMake.

function(pa_pokesim_map_directory OUT GAME CONSUMER SOURCE)
    if(NOT GAME STREQUAL "frlg" AND NOT GAME STREQUAL "bdsp")
        message(FATAL_ERROR "Unknown PokemonSimulation map game: ${GAME}")
    endif()
    find_package(Python3 3.8 REQUIRED COMPONENTS Interpreter)
    get_filename_component(TOOLS "${CMAKE_CURRENT_FUNCTION_LIST_DIR}/../.." ABSOLUTE)
    execute_process(
        COMMAND "${CMAKE_COMMAND}" -E env "PYTHONPATH=${TOOLS}/src"
            "${Python3_EXECUTABLE}" -m pokesim.maps.consumer_sync check
            --layout resources --consumer "${CONSUMER}" --source "${SOURCE}" --offline
        RESULT_VARIABLE STATUS OUTPUT_VARIABLE OUTPUT ERROR_VARIABLE ERROR
    )
    if(NOT STATUS EQUAL 0)
        message(FATAL_ERROR "Map resources are missing, modified or unapproved. Prepare the pinned lock before configuring.\n${OUTPUT}${ERROR}")
    endif()
    set(FOLDER "${CONSUMER}/Packages/Resources/Pokemon/Maps/${GAME}")
    if(NOT EXISTS "${FOLDER}/PROVENANCE.txt")
        message(FATAL_ERROR "No prepared map resource pin for ${GAME}.")
    endif()
    file(GLOB MAP_FILES CONFIGURE_DEPENDS "${FOLDER}/*")
    set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS
        "${CONSUMER}/devtools/maps/map-resources.lock.json" ${MAP_FILES})
    set(${OUT} "${FOLDER}" PARENT_SCOPE)
endfunction()
