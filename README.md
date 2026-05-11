# Adeeb_FastAPI
An Iteration for Adeeb's RESTful API using Python, FastAPI and Postgres.


## Setup

- Setup your virtual environment:
```sh
$ python -m venv .venv
```

- use the virtual environment with poetry
```sh
$ poetry env use .venv/bin/python3
```

- Install project packages:
```sh
$ poetry install 
```

- Run the app:
```sh
$ poetry run uvicorn adeeb_fastapi.main:app --reload
```
