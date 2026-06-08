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

- Used Podman for containerization instead of Docker, used Containerfile and compose.yaml for that.

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

- Create JWT public & private keys:
    - with openssl:
        ```sh
        $ openssl genrsa -out jwt_private_rsa256.key 4096 
        $ openssl rsa -in jwt_private_rsa256.key -pubout -out jwt_public_rsa256.key
        ```
    - with ssh-keygen:
        ```sh
        $ ssh-keygen -t rsa -b 4096 -m PEM -f jwt_private_rsa256.key   
        $ ssh-keygen -f jwt_private_rsa256.key -e -m PKCS8 > jwt_public_rsa256.key
        ```

- Run the app for development:
    - use shorthand script, that runs uvicorn:
        ```sh
        $ pdm run dev
        ```
    - directly with uvicorn:
        ```sh
        $ pdm run uvicorn adeeb_fastapi.main:app --reload
        ```
    - directly with FastAPI CLI:
        ```sh
        $ pdm run fastapi dev adeeb_fastapi/main.py
        ```
    - use Podman for containerization:
        ```sh
        podman-compose -f compose.yaml up
        ```