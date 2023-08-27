#!/bin/bash

exec uvicorn webserver.app:app --port  "${AUTORIM_PORT:-8061}" --host "0.0.0.0"