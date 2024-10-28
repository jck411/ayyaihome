#!/bin/bash

# Navigate to the backend directory and start Uvicorn
cd ~/ayyaihome
uvicorn main:app --reload &

# Navigate to the frontend directory and start npm
cd ~/ayyaihome/frontend
npm start
