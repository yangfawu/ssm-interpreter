#!/bin/bash

MAX_RUN_TIME=10s

for name in $(ls input)
do
    echo [$name]
    timeout $MAX_RUN_TIME python ssm_interpreter.py input/$name
    if [[ $? == 124 ]]
    then
        echo "Program execution killed after running for $MAX_RUN_TIME"
    fi
    echo
done
