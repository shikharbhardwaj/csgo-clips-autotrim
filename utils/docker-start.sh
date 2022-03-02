#!/bin/bash

docker run --user $(id -u):$(id -g) -v $(pwd):/tf/code -it --gpus all -p 8888:8888 csgo-clips-autotrim

