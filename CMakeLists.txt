#
# This software is supplied under the terms of the MIT License, a
# copy of which should be located in the distribution where this
# file was obtained (LICENSE.txt).  A copy of the license may also be
# found online at https://opensource.org/licenses/MIT.

cmake_minimum_required (VERSION 2.8.7)

project(nanomq-ci)

SET(CMAKE_C_FLAGS  "-g")

set(NNG_PROTO_MQTT_CLIENT ON)

if(NNG_ENABLE_TLS)
    add_definitions(-DNNG_SUPP_TLS)
endif()

add_subdirectory(nng)

add_executable(nanomq-ci main.c utils.c nnc_opt.c nnc_test.c)
target_link_libraries(nanomq-ci nng)
add_dependencies(nanomq-ci nng)

