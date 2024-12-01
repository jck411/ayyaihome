


fuser -k 8000/tcp

git add .

git commit -m "comment" 

git push -u origin startagain.3

git pull --rebase origin startagain.3


git reset --hard HEAD
git clean -f

from root
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload



export PYTHONPATH=$(pwd)
/home/jack/aaaVENVs/aihome/bin/python3 backend/main.pys


export PYTHONPATH=/home/jack/ayyaihome
python /home/jack/ayyaihome/backend/main.py


from backend.config import *

