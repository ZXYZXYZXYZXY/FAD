add_library(gurobi_emitter gurobi_emitter.cpp)
target_link_libraries(gurobi_emitter ilp_model)

add_library(ilp_model_builder ilp_model_builder.cpp)