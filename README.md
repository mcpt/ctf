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
2. Go to mCTF/docker_config.py, Set DEBUG to True and root to "http://localhost:28730" as well as deleting import config2.
3. docker build -t mctf .
4. docker run -p 28730:28730 mctf
5. docker exec -it <container_id> /bin/bash
6. Run

```
. .venv/bin/activate
python manage.py migrate
python manage.py createsuperuser
```


## Troubleshooting
- If Django hangs while booting (e.g. no response comes from uWSGI, or worker is killed frequently in Gunicorn), it may be hanging trying to connect to the cluster.
