cmake_minimum_required(VERSION 2.6)
project (logparser)
SET (Internet2-FIB-Analyzer_VERSION_MAJOR 1)
SET (Internet2-FIB-Analyzer_VERSION_MINOR 0)
SET (GCC_COVERAGE_COMPILE_FLAGS "-std=c++11")
SET (CMAKE_CXX_FLAGS "${GCC_COVERAGE_COMPILE_FLAGS}")

if (DEBUG)
  message ("enable debug mode...")
  SET (GCC_COVERAGE_COMPILE_FLAGS "-std=c++11 -g")
else ()
  message ("g++ optimize to -O3")
  SET (GCC_COVERAGE_COMPILE_FLAGS "-std=c++11 -O3")
endif ()

SET (CMAKE_CXX_FLAGS  "${GCC_COVERAGE_COMPILE_FLAGS}" )

include_directories (".")

add_executable (logparser logparser.cpp)

add_library(entity SHARED entity.cpp)
add_library(parser SHARED parser.cpp)
target_link_libraries(logparser dl)

add_subdirectory("parsers")

add_custom_target(mk_parser_dir ALL mkdir -p parsers/)
set(rule_link_parser_path "parsers/rule_link_parser/librule_link_parser.so")
set(topology_parser_path "parsers/topology_parser/libtopology_parser.so")
set(anomaly_parser_path "parsers/anomaly_parser/libanomaly_parser.so")
set(localization_parser_path "parsers/localization_parser/liblocalization_parser.so")
set(constraint_parser_path "parsers/constraint_parser/libconstraint_parser.so")
add_custom_target(copy_rule_link_parser ALL cp ${rule_link_parser_path} parsers/librule_link_parser.so DEPENDS rule_link_parser)
add_custom_target(copy_topology_parser ALL cp ${topology_parser_path} parsers/libtopology_parser.so DEPENDS topology_parser)
add_custom_target(copy_anomaly_parser ALL cp ${anomaly_parser_path} parsers/libanomaly_parser.so DEPENDS anomaly_parser)
add_custom_target(copy_localization_parser ALL cp ${localization_parser_path} parsers/liblocalization_parser.so DEPENDS localization_parser)
add_custom_target(copy_constraint_parser ALL cp ${constraint_parser_path} parsers/libconstraint_parser.so DEPENDS constraint_parser)

