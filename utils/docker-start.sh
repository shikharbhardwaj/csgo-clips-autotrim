#!/bin/bash

set -eouf pipefail

WANDB_API_KEY=$(./wandb_api_key.sh)
ENV_DIR=$(mktemp -d)
ENV_FILE="$ENV_DIR/env.json"

echo $ENV_FILE

function finish {
    # Cleanup code.
    echo "Exiting"
    rm "$ENV_FILE"
}

trap finish EXIT

docker run -v $(pwd):/code \
    -e "TRANSFORMERS_CACHE=/tmp/transformers_cache" \
    -e "WANDB_DOCKER=1" \
    -e "WANDB_API_KEY=$WANDB_API_KEY" \
    -v $(pwd)/.local/cache/transformers_cache:/tmp/transformers_cache \
    -v "$ENV_DIR:/env" \
    -it \
    --gpus all \
    -p 8888:8888 \
    -e MY_USERNAME=shikhar \
    -e MY_GROUP=shikhar \
    -e MY_UID=$(id -u) \
    -e MY_GID=$(id -g) \
    csgo-clips-autotrim:pytorch jupyter lab --ip "0.0.0.0"
