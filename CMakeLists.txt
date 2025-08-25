cmake_minimum_required(VERSION 3.16)
project(glacium_fsfw CXX)

add_library(fsfw
    src/fsfw/serviceinterface/ServiceInterface.cpp
)

target_include_directories(fsfw PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/src)
