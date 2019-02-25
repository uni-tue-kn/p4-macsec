BMV2_SWITCH_EXE = ../vm/behavioral-model/targets/simple_switch_grpc/simple_switch_grpc
#NO_P4 = true
P4C_ARGS = --emit-externs --p4runtime-file $(basename $@).p4info --p4runtime-format text

run_args += --cpu-port 16

include ../utils/Makefile
