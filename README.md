# Odmozdzacze
![Lines of code](https://img.shields.io/tokei/lines/github/chimekkoo/odmozdzacze)
![License](https://img.shields.io/github/license/chimekkoo/odmozdzacze)
![Website](https://img.shields.io/website?down_color=lightgrey&down_message=offline&up_color=green&up_message=online&url=https%3A%2F%2Fodmozdzacze.pl)

## General info
Odmozdzacze is a polish web app for reporting brain-wasting apps, games, cartoons, etc.
More info on the main page `app/templates/index.html` (in polish).

## Running (Docker)
Clone the repo:
```
git pull https://github.com/ChimekKoo/odmozdzacze.git
cd odmozdzacze
```
Create `.env` file with the app configuration (remember to use Google reCAPTCHA v2, not v3):
```
ODMOZDZACZE_RECAPTCHA_SITE_KEY="<recaptcha-site-key>"
ODMOZDZACZE_RECAPTCHA_SECRET_KEY="<recaptcha-secret-key>"
ODMOZDZACZE_SESSION_KEY="<random-alphanumeric-string>"
```
(Optional:) Build the image yourself (e.g. if your CPU architecture is not supported by the prebuilt image, see [here](https://ghcr.io/chimekkoo/odmozdzacze))
```
docker compose build
```
And run the stack:
```
docker compose up -d
```

## Development (linux/mac)
Clone the repo and write the `.env` file as above, but add `ODMOZDZACZE_DEBUG=true` option.
Then:
```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd app
# [ write some code... ]
python3 wsgi.py
```
