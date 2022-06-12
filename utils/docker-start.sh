#!/bin/bash

docker run -v $(pwd):/code \
    -e "TRANSFORMERS_CACHE=/tmp/transformers_cache" \
    -e "WANDB_DOCKER=1" \
    -e "WANDB_API_KEY=$(./pass.sh)" \
    -v $(pwd)/.local/cache/transformers_cache:/tmp/transformers_cache \
    -it \
    --gpus all \
    -p 8888:8888 \
    -e MY_USERNAME=shikhar \
    -e MY_GROUP=shikhar \
    -e MY_UID=$(id -u) \
    -e MY_GID=$(id -g) \
    csgo-clips-autotrim:pytorch jupyter lab --ip "0.0.0.0"
