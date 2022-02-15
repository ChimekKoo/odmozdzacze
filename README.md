# Odmozdzacze
![Discord](https://img.shields.io/discord/788341540438933554?color=%237289DA&label=discord&logo=discord&logoColor=%23ffffff)
![Lines of code](https://img.shields.io/tokei/lines/github/odmozdzacze/odmozdzacze)
![License](https://img.shields.io/github/license/odmozdzacze/odmozdzacze)
![Framework](https://img.shields.io/badge/built_with-flask-informational)

## Table of contents
  - [General info](#general-info)
  - [Technologies](#technologies)
  - [Setup](#setup)
  - [Status](#status)
  - [Contact](#contact)

## General info
Odmozdzacze is a polish service dedicated for reporting brain-wasting apps, games, cartoons, etc.
More info on the main page `templates/index.html` (unfortunetely in polish).

## Technologies
- Python 3.8
- Flask 1.1.2
- MongoDB and PyMongo 3.11  
- the rest of the dependencies in `requirements.txt`.
  
## Setup
**On Ubuntu linux:**  
Set environment variables `ODMOZDZACZE_MONGODB_URL` to your mongodb connection url and `ODMOZDZACZE_SECRETKEY` to a session secret key (it can be just a random string).
```
git pull git@github.com:odmozdzacze/odmozdzacze
cd odmozdzacze
python3 -m venv venv
source venv/bin/activate
pip3 installl -r requirements.txt
python3 main.py
```
**On Docker:**  
Not available yet.

## Status
Not stable

## Contact
Feel free to contact us [here](https://docs.google.com/forms/d/e/1FAIpQLSclAWhzF7YhCIZqWfmHAMA1Y-f6VHzqV2qb75RPhDT4m2ubVQ/viewform?usp=sf_link).
