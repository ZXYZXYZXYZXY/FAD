add_library(option_parser_interface option_parser_interface.cpp)
add_library(option_parser option_parser.cpp)
target_link_libraries(option_parser option_parser_interface)

add_library(boost_option_parser boost_option_parser.cpp)
target_link_libraries(boost_option_parser option_parser_interface boost_program_options boost_system boost_filesystem)

add_library(interface_parser interface_parser.cpp)
add_library(juniper_interface_parser juniper_interface_parser.cpp)
target_link_libraries(juniper_interface_parser interface_parser)

add_library(rule_parser rule_parser.cpp)
add_library(route_parser route_parser.cpp)
add_library(juniper_rule_parser juniper_rule_parser.cpp)
target_link_libraries(juniper_rule_parser rule_parser route_parser)
