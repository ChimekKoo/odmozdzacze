# Odmozdzacze
![Discord](https://img.shields.io/discord/788341540438933554?color=%237289DA&label=discord&logo=discord&logoColor=%23ffffff)
![Lines of code](https://img.shields.io/tokei/lines/github/odmozdzacze/odmozdzacze)
![License](https://img.shields.io/github/license/odmozdzacze/odmozdzacze)
![Framework](https://img.shields.io/badge/built_with-flask-informational)
![Website](https://img.shields.io/website?down_color=lightgrey&down_message=offline&up_color=green&up_message=online&url=http%3A%2F%2Fodmozdzacze.pl)

## Table of contents
  - [General info](#general-info)
  - [Technologies](#technologies)
  - [Setup](#setup)
  - [Status](#status)
  - [Contact](#contact)

## General info
Odmozdzacze is a polish service dedicated for reporting brain-wasting apps, games, cartoons, etc.
More info on the main page `app/templates/index.html` (in polish).

## Technologies
- Python 3.8
- Flask
- MongoDB and PyMongo
- the rest of the dependencies in `requirements.txt`.
  
## Setup (only for development, production server is not ready yet)
**On Ubuntu linux:**  
Set environment variables (you can use also `.env` file):
- `ODMOZDZACZE_MONGODB_URL` to your mongodb connection url,
- `ODMOZDZACZE_SECRET_KEY` to a session secret key (it can be just a random string),
- `ODMOZDZACZE_RECAPTCHA_SITE_KEY` to your reCAPTCHA v2 site key,
- `ODMOZDZACZE_RECAPTCHA_SECRET_KEY` to your reCAPTCHA v2 secret key
```
git pull https://github.com/ChimekKoo/odmozdzacze.git
cd odmozdzacze
pip3 installl -r requirements.txt
python3 app/wsgi.py
```
**On Docker:**  
Not available yet, but you can build and run the image yourself. Website inside the container is served on `8000` port.

## Status
Production server is not ready yet.

## Contact
Feel free to contact us [here](https://docs.google.com/forms/d/e/1FAIpQLSclAWhzF7YhCIZqWfmHAMA1Y-f6VHzqV2qb75RPhDT4m2ubVQ/viewform?usp=sf_link).
