from flask import Flask, render_template, send_file, request, redirect, url_for, abort, session, make_response
from os.path import isfile
from pymongo import MongoClient
from smtplib import SMTP
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from json import loads
from random import randint
from datetime import datetime
from magic import Magic

import constants


cred_file_obj = open("cred.json", "r")
cred = loads(cred_file_obj.read())
cred_file_obj.close()

smtp_cred = cred["smtp"]


app = Flask(__name__)
app.secret_key = cred["secret_key"]

mongo_client = MongoClient(cred["mongodb"]["url"])
db = mongo_client["odmozdzacze"]
reports_col = db["reports"]
categories_col = db["categories"]
admins_col = db["admins"]

magic = Magic(mime=True)


blank_reportdict = {
    "category": "",
    "name": "",
    "content": "",
    "email": ""
}


def generate_id(ids):
    while True:
        random_number = randint(100000000, 999999999)
        if random_number not in ids:
            return str(random_number)


def check_if_logged():
    try:
        session["logged"]
    except KeyError:
        logged = False
    else:
        if not session["logged"]:
            logged = False
        logged = True
    return logged


def cursor_to_list(cursor, cursor_filter=""):
    if cursor_filter == "":
        array = []
        for i in cursor:
            array.append(i)
        return array
    else:
        array = []
        for i in cursor:
            array.append(i[cursor_filter])
        return array


def request_args_to_dict(available_request_args):
    request_args = {}

    for request_arg in available_request_args.keys():
        if request_arg in request.args.keys():
            request_args[request_arg] = request.args[request_arg]
        else:
            request_args[request_arg] = available_request_args[request_arg]

    return request_args


@app.errorhandler(404)
def error_404(error):
    if request.url.startswith("/api"):
        return make_response({
            "error": "404 Not Found",
            "description": "Resource not found - check url."
        })
    else:
        return render_template("404.html", error=error, admin=check_if_logged(), url=constants.BASE_URL)


@app.route("/")
def index():
    return render_template("index.html", admin=check_if_logged(), url=constants.BASE_URL)


@app.route("/images/<image>")
def images(image):
    if isfile(f"templates/images/{image}.png"):
        return send_file(f"templates/images/{image}.png", mimetype="image/png")
    else:
        abort(404)


@app.route("/files/<filename>")
def files_odmozdzacze_logo(filename):
    if isfile("templates/files/" + filename):
        magic_mimetype = magic.from_file("templates/files/" + filename)
        return send_file("templates/files/" + filename, mimetype=magic_mimetype)
    else:
        abort(404)


@app.route("/fontello/css/fontello.css")
def fontello_css_fontellocss():
    return send_file("templates/fontello/css/fontello.css")


@app.route("/about")
def about():
    return render_template("about.html", admin=check_if_logged(), url=constants.BASE_URL)


@app.route("/ranking")
def ranking():
    result = cursor_to_list(reports_col.find())
    ranking_reports = []

    for ranking_report in result:
        if ranking_report["verified"]:
            ranking_reports.append(ranking_report)

    return render_template("ranking.html", ranking_reports=ranking_reports, url=constants.BASE_URL)


@app.route("/browse")
def browse():

    request_args = request_args_to_dict({"q": "", "category": "", "per-page": "10", "verified": "on"})

    if request_args["verified"] == "verified":
        request_args["verified"] = True
    elif request_args["verified"] == "unverified":
        request_args["verified"] = False
    else:
        request_args["verified"] = ""

    request_args["q"] = request_args["q"].lower()

    elements = cursor_to_list(reports_col.find({
        "name": request_args["q"],
        "category": request_args["category"],
        "verified": request_args["verified"]
    }))

    per_page = str(request_args["per-page"])

    try:
        per_page = int(per_page)
    except ValueError:
        per_page = len(elements)

    if len(elements) > per_page:
        elements = elements[:per_page]

    return render_template("browse.html", elements=elements, categories=cursor_to_list(categories_col.find(), "name"), admin=check_if_logged(), elements_len=len(elements), url=constants.BASE_URL)


@app.route("/developer")
def developer():
    return render_template("developer.html", admin=check_if_logged(), url=constants.BASE_URL)


@app.route("/contact")
def contact():
    return render_template("contact.html", admin=check_if_logged(), url=constants.BASE_URL)


@app.route("/showreport/<reportid>")
def show_report(reportid):
    result = cursor_to_list(reports_col.find({"id": reportid}))
    if len(result) != 1:
        abort(404)
    return render_template("show_report.html", reportdict=result[0], admin=check_if_logged(), url=constants.BASE_URL)


@app.route("/verifyreport/<reportid>")
def verify_report(reportid):
    result = cursor_to_list(reports_col.find({"id": reportid}))
    if len(result) != 1:
        abort(404)
    else:
        if check_if_logged():
            reports_col.update_one({"id": reportid}, {"$set": {
                "verified": True
            }})
            return redirect(url_for("browse"))
        else:
            return redirect(url_for("login"))


@app.route("/unverifyreport/<reportid>")
def unverify_report(reportid):
    result = cursor_to_list(reports_col.find({"id": reportid}))
    if len(result) != 1:
        abort(404)
    else:
        if check_if_logged():
            reports_col.update_one({"id": reportid}, {"$set": {
                "verified": False
            }})
            return redirect(url_for("browse"))
        else:
            return redirect(url_for("login"))


@app.route("/deletereport/<reportid>")
def delete_report(reportid):
    result = cursor_to_list(reports_col.find({"id": reportid}))
    if len(result) != 1:
        abort(404)
    else:
        if check_if_logged():
            reports_col.delete_one({"id": reportid})
            return redirect(url_for("browse"))
        else:
            return redirect(url_for("login"))


@app.route("/editreport/<reportid>", methods=["GET", "POST"])
def edit_report(reportid):
    result = cursor_to_list(reports_col.find({"id": reportid}))
    if len(result) != 1:
        abort(404)
    else:
        if not check_if_logged():
            return redirect(url_for("login"))
        else:

            if request.method == "POST":

                if request.form["category"] == ""\
                 or request.form["name"] == ""\
                 or request.form["content"] == ""\
                 or request.form["email"] == "":
                    result = cursor_to_list(reports_col.find({"id": reportid}))
                    if len(result) != 1:
                        abort(404)
                    return render_template("report.html", error="Nie wybrałeś kategorii lub nie wypełniłeś któregoś pola.", reportdict=result[0], admin=check_if_logged(), url=constants.BASE_URL)
                else:

                    reports_col.update_one({"id": reportid}, {
                        "$set": {
                            "category": request.form["category"],
                            "name": request.form["name"],
                            "content": request.form["content"],
                            "email": request.form["email"]
                        }
                    })

                    categories = cursor_to_list(categories_col.find(), "name")

                    result = cursor_to_list(reports_col.find({"id": reportid}))
                    if len(result) != 1:
                        abort(404)

                    return render_template("edit_report.html", status="Edytowano pomyślnie.", categories=categories, reportdict=result[0], admin=check_if_logged(), url=constants.BASE_URL)

            else:

                categories = cursor_to_list(categories_col.find(), "name")

                result = cursor_to_list(reports_col.find({"id": reportid}))
                if len(result) != 1:
                    abort(404)

                return render_template("edit_report.html", categories=categories, reportdict=result[0], admin=check_if_logged(), url=constants.BASE_URL)


@app.route("/report", methods=["GET", "POST"])
def report():
    if request.method == "POST":

        if request.form["category"] == ""\
         or request.form["name"] == ""\
         or request.form["content"] == ""\
         or request.form["email"] == "":
            return render_template("report.html", error="Nie wybrałeś kategorii lub nie wypełniłeś któregoś pola.", admin=check_if_logged(), url=constants.BASE_URL)
        else:

            report_date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            ids = cursor_to_list(reports_col.find(), "id")
            report_id = generate_id(ids)

            reports_col.insert_one({
                "id": report_id,
                "datetime": report_date_time,
                "category": request.form["category"],
                "name": request.form["name"],
                "content": request.form["content"],
                "email": request.form["email"],
                "verified": False
            })

            msg = MIMEMultipart("alternative")
            msg['Subject'] = "Wiadomość od Odmóżdżacze"
            msg['From'] = smtp_cred["login"]
            msg['To'] = request.form["email"]
            msg.attach(MIMEText(f"""
            Odmóżdżacz zgłoszony!

            ID: {report_id}
            Czas: {report_date_time}
            Kategoria: {request.form["category"]}
            Nazwa: {request.form["name"]}
            Opis: {request.form["content"]}
            """))

            smtp_obj = SMTP(smtp_cred["host"], smtp_cred["port"])

            smtp_obj.ehlo()
            smtp_obj.starttls()
            smtp_obj.login(smtp_cred["login"], smtp_cred["password"])
            smtp_obj.sendmail(smtp_cred["login"], request.form["email"], msg.as_string())
            smtp_obj.quit()

            del smtp_obj

            categories = cursor_to_list(categories_col.find(), "name")

            return render_template("report.html", status="Zgłoszono pomyślnie.", categories=categories, admin=check_if_logged(), reportdict=blank_reportdict, url=constants.BASE_URL)

    elif request.method == "GET":

        reportdict = request_args_to_dict({"category": "", "name": "", "content": "", "email": ""})

        categories = cursor_to_list(categories_col.find(), "name")
        return render_template("report.html", categories=categories, admin=check_if_logged(), reportdict=reportdict, url=constants.BASE_URL)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":

        if request.form["login"] == "" or request.form["password"] == "":
            return render_template("login.html", error="Nie wypełniłeś któregoś pola.", admin=check_if_logged(), url=constants.BASE_URL)
        else:
            username = request.form["login"]
            password = request.form["password"]

            result = admins_col.find({"login": username, "password": password})
            result_list = []

            for j in result:
                result_list.append(j)

            if len(result_list) != 1:
                return render_template("login.html", error="Nieprawidłowy login lub hasło.", admin=check_if_logged(), url=constants.BASE_URL)

            session["logged"] = True

            return redirect(url_for("index"))

    else:
        if check_if_logged():
            return redirect(url_for("index"))
        else:
            return render_template("login.html", admin=check_if_logged(), url=constants.BASE_URL)


@app.route("/logout")
def logout():
    if check_if_logged():
        session.pop("logged", None)
        return redirect(url_for("index"))
    else:
        return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port="8000", debug=True)
