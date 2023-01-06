#!/bin/bash

# Install pip
sudo apt-get install -y python3-pip

# Install the required dependencies
pip install -r requirements.txt

# Run the script
python main_v4.py
