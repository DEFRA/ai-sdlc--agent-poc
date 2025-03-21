#!/bin/bash

# Script to start the FastAPI development server with auto-reload enabled
clear && uvicorn src.main:app --reload 