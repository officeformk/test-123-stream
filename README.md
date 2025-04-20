# homeoAssistAI

source '/Users/mayurkothawade/homeoenv/bin/activate'
pip3 install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
