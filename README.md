# sheet-api
Wrapper for some sheet shenanigans

### Running
```sh
 python3 -m virtualenv --python=3.10.6 venv
 source ./venv/bin/activate
 python3 -m pip install -r requirements.txt
 gunicorn -w 4 -b 127.0.0.1:5000 --chdir <path_to_app.py> wsgi:app
```

### Usage

Navigate to `api.jstitt.dev/acmmm/sheet/docs`

To use any `POST` routes you need to head over to `api.jstitt.dev/acmmm/sheet/login` and use admin (secret) credentials to retrieve a JWT key.

Any `POST` requests need to be made with an authorization header as follows:
`Authorization: Bearer <your_jwt_key>`

*Note: Endpoints prefix is `api.jstitt.dev/acmmm/sheet/`*

### Setting up GCP VM to host webserver:
Also a template for GCP + Caddy + Flask + Gunicorn web servers
* Create f1-micro VM instance
* setup ssh keys (https://www.markusdosch.com/2019/03/how-to-deploy-a-python-flask-application-to-the-web-with-google-cloud-platform-for-free/)
```
# setting up ssh keys
ssh-keygen -t rsa -b 4096 -C "<username>"
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_rsa
```
* Don't forget to add key to GCP VM instance via `SSH Keys` in VM config
* Clone flask app
* Setup Caddyfile (reverse proxy + routing)
* spin up WSGI with Gunicorn
* Configure systemctl `see ./systemd`
