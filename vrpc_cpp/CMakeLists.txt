cmake_minimum_required(VERSION 3.16)
project(fsbq)

add_library(fsbq SHARED
    src/fsb_queue_consumer.cpp
    src/fsb_queue_producer.cpp
    )

target_include_directories(fsbq
    PUBLIC inc
    )

add_executable(fsbq_tester
    src/fsb_queue_tester.cpp
    )
target_link_libraries(fsbq_tester
    PRIVATE fsbq
    )