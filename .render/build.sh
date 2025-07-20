#!/usr/bin/env bash

# Manually install correct Python version
pyenv install 3.10.13
pyenv global 3.10.13

# Install dependencies
pip install -r requirements.txt
