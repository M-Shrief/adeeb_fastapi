# Adeeb_FastAPI
An Iteration for Adeeb's RESTful API using Python, FastAPI and Postgres.

## Roadmap
- Make this iteration the primary one instead of Nodejs iteration
- Hardening security:
	- Requiring JWT token for PUT/DELETE requests
	- Handling Top 10 OWASP security threats.

## Changes
Changes from primary iteration:
- Instead of making a custom type for verses, we use a normal array and add another field is_couplet. And in this way we improve our support for other poems that uses lines rather than couplets

- Changed Naming for:
    - `poet` into `adeeb`, as it includes all of them even the ones that create poems, and it's more aligned with the identity of the project
    - `proses` into `prose_qoutes`
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
