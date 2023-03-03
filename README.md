# sheet-api
Wrapper for some sheet shenanigans


Also a template for GCP + Caddy + Flask + Gunicorn web servers


Setting up GCP VM to host webserver:
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
