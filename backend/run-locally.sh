# To run:
# create a venv:
#    python3 -m venv .venv
#    source .venv/bin/activate
# install requirements:
#    pip install -r requirements.txt

# now use this to run locally:
uvicorn app.main:app --reload --port 8001
