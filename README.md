mCTF
=====
A platform to host as many CTF contests and problems as you want.

## Features
- Admin Interface to add Problems, Contests, Organizations, etc.
- Contests for individuals, or enable participants to team up
- Public Problems for everyone to view and solve outside of contests

## Installation
Installation instructions are currently a work in progress. Feel free to join [our Discord](https://discord.gg/cXzz9eR) if you have any questions.


## Development Setup
1. Clone the repository
### Using Poetry (Recommended) 
2. Run `pip install poetry`
3. Run `poetry install`
4. Run `poetry shell`
5. Create a file called config.py with the contents of [Docker Setup #2](#using-docker) 
5. Run `python manage.py migrate && python manage.py createsuperuser`
6. To start the server, run `python manage.py runserver`

### Using Docker
2. Go to mCTF/docker_config.py, Set DEBUG to True and root to "http://localhost:28730" as well as deleting import config2.
3. docker build -t mctf .
4. docker run -p 28730:28730 mctf
5. docker exec -it <container_id> /bin/bash
6. 

```
. .venv/bin/activate
python manage.py migrate
python manage.py createsuperuser
```
7. in the docker container, go to /public/scss and delete all *.css files (`rm *.css`)


## Troubleshooting
- If Django hangs while booting (e.g. no response comes from uWSGI, or worker is killed frequently in Gunicorn), it may be hanging trying to connect to the cluster.
