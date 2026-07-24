#!/usr/bin/env bash
exec >ChOp_log.txt 2>&1

# prior to running this script, run the system-specific equivalent of
# source ../chapel/util/setchplenv.bash

export MACHINE_TYPE="$(uname -m)"

make queens_singlelocale_cpu

echo "********** No SMT"
for i in $(seq 1 10);
do
  ./bin/queens_mcore.out --data_structure="bitset" --size=19 --initial_depth=5  --mode=mcore --slchunk=1
done

export MACHINE_TYPE="$(uname -m)"
if [ ${MACHINE_TYPE} == 'x86_64' ];
then
  # Set up some variables to use for testing with SMT and/or restricting to a single socket.
  # Assume 2 logical threads per core and 2 sockets since that's true of all the x86 machines we're testing with.
  export NUM_LOGICAL_THREADS=$(nproc --all)
  export NUM_CORES=$(($NUM_LOGICAL_THREADS / 2))
  export NUM_CORES_PER_SOCKET=$(($NUM_LOGICAL_THREADS / 4))
  export SOCKET_TASKSET_RANGE="0-$(($NUM_CORES_PER_SOCKET - 1)),$NUM_CORES-$(($NUM_CORES + $NUM_CORES_PER_SOCKET - 1))"
  
  # All hyperthreads
  echo "********** SMT"
  export CHPL_RT_NUM_THREADS_PER_LOCALE=MAX_LOGICAL
  for i in $(seq 1 10);
  do
    ./bin/queens_mcore.out --data_structure="bitset" --size=19 --initial_depth=5  --mode=mcore --slchunk=1 --num_threads=$NUM_LOGICAL_THREADS
  done

  # single socket, no hyperthreads
  echo "********** Single Socket, no SMT"
  for i in $(seq 1 10);
  do
    taskset -c $SOCKET_TASKSET_RANGE ./bin/queens_mcore.out --data_structure="bitset" --size=19 --initial_depth=5  --mode=mcore --slchunk=1 --num_threads=$NUM_CORES_PER_SOCKET
  done

  # single socket with hyperthreads
  echo "********** Single Socket, with SMT"
  for i in $(seq 1 10);
  do
    taskset -c $SOCKET_TASKSET_RANGE ./bin/queens_mcore.out --data_structure="bitset" --size=19 --initial_depth=5  --mode=mcore --slchunk=1 --num_threads=$NUM_CORES
  done
fi

# The only ARM system we're testing has two sockets, so just assume that here.
if [ ${MACHINE_TYPE} == 'aarch64' ];
then
  export NUM_CORES=$(nproc --all)
  export NUM_CORES_PER_SOCKET=$(($NUM_CORES / 2))
  export SOCKET_TASKSET_RANGE="0-$(($NUM_CORES_PER_SOCKET - 1))"
  export CHPL_TEST_PERF_DIR="$CHPL_HOME/test/perfdat/clbg_comparison_single_socket"
  export CHPL_RT_NUM_THREADS_PER_LOCALE=$NUM_CORES_PER_SOCKET
  echo "********** Single Socket"
  for i in $(seq 1 10);
  do
    ./bin/queens_mcore.out --data_structure="bitset" --size=19 --initial_depth=5  --mode=mcore --slchunk=1 --num_threads=$NUM_CORES_PER_SOCKET
  done
fi
