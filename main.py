from asyncio import QueueEmpty
from tkinter.tix import Tree
from flask import Flask, render_template, request, redirect, url_for, abort, session, jsonify
from datetime import datetime
import werkzeug
import url64

from constants import *
from cred import get_cred
from utils import *
from db import reports_col, categories_col, admins_col


cred = get_cred()

app = Flask(__name__)
app.secret_key = cred["secret_key"]


blank_reportdict = {
    "id": "",
    "edittime": "",
    "inserttime": "",
    "category": "",
    "name": "",
    "content": "",
    "email": "",
    "verified": ""
}


@app.errorhandler(404)
def error_404(e):
    redirect_to = url64.encode(request.url)
    if request.url.startswith(API_ENTRYPOINT):
        return jsonify({
            "error": "404 Not Found",
            "description": "Resource not found - check url."
        }), 404
    else:
        return render_template("error.html", error_code="404", error_name="Nie znaleziono", admin=check_if_logged(), redirect_to=redirect_to)


@app.route("/")
def index():
    redirect_to = url64.encode(request.url)
    return render_template("index.html", admin=check_if_logged(), redirect_to=redirect_to)

@app.route("/ranking")
def ranking():
    redirect_to = url64.encode(request.url)
    # result = cursor_to_list(reports_col.find())
    result = []

    return render_template("ranking.html", ranking_reports=result, admin=check_if_logged(), redirect_to=redirect_to)


@app.route("/browse")
def browse():
    redirect_to = url64.encode(request.url)

    categories = cursor_to_list(categories_col.find(), "name")

    query = {}
    fields = {"name": "", "category": "", "verified": ""}

    try:
        request.args["q"]
    except KeyError:
        pass
    else:
        query["name"] = {"$regex": request.args["q"].lower()}
        fields["name"] = request.args["q"].lower()

    try:
        request.args["category"]
    except KeyError:
        pass
    else:
        if request.args["category"] in categories:
            query["category"] = request.args["category"]
            fields["category"] = request.args["category"]
    
    try:
        request.args["verified"]
    except KeyError:
        pass
    else:
        if request.args["verified"] == "verified":
            query["verified"] = True
            fields["verified"] = True
        elif request.args["verified"] == "unverified":
            query["verified"] = False
            fields["verified"] = False

    if query == {}:
        query = {"verified": True}
        fields["verified"] = True
    
    elements = cursor_to_list(reports_col.find(query))

    return render_template("browse.html",
                           elements=elements,
                           fields=fields,
                           categories=categories,
                           admin=check_if_logged(),
                           redirect_to=redirect_to)


@app.route("/developer")
def developer():
    redirect_to = url64.encode(request.url)
    return render_template("developer.html", admin=check_if_logged(), redirect_to=redirect_to)


@app.route("/contact")
def contact():
    redirect_to = url64.encode(request.url)
    return render_template("contact.html", admin=check_if_logged(), redirect_to=redirect_to)


@app.route("/showreport/<reportid>")
def show_report(reportid):
    redirect_to = url64.encode(request.url)
    result = cursor_to_list(reports_col.find({"id": reportid}))
    if len(result) != 1:
        abort(404)
    return render_template("show_report.html", reportdict=result[0], admin=check_if_logged(), redirect_to=redirect_to)


@app.route("/verifyreport/<reportid>")
def verify_report(reportid):
    redirect_to = url64.encode(request.url)
    result = cursor_to_list(reports_col.find({"id": reportid}))
    if len(result) != 1:
        abort(404)
    else:
        if check_if_logged():
            reports_col.update_one({"id": reportid}, {"$set": {
                "verified": True
            }})
            return redirect(url_for("show_report", reportid=reportid))
        else:
            return redirect(url_for("login"))


@app.route("/unverifyreport/<reportid>")
def unverify_report(reportid):
    redirect_to = url64.encode(request.url)
    result = cursor_to_list(reports_col.find({"id": reportid}))
    if len(result) != 1:
        abort(404)
    else:
        if check_if_logged():
            reports_col.update_one({"id": reportid}, {"$set": {
                "verified": False
            }})
            return redirect(url_for("show_report", reportid=reportid))
        else:
            return redirect(url_for("login"))


@app.route("/deletereport/<reportid>")
def delete_report(reportid):
    redirect_to = url64.encode(request.url)

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
    redirect_to = url64.encode(request.url)

    result = cursor_to_list(reports_col.find({"id": reportid}))
    if len(result) != 1:
        abort(404)
    else:
        if not check_if_logged():
            return redirect(url_for("login"))
        else:

            if request.method == "POST":

                try:
                    category = request.form["category"]
                except werkzeug.exceptions.BadRequestKeyError:
                    category = ""

                if request.form["category"] == "" \
                 or request.form["name"] == "" \
                 or request.form["content"] == "" \
                 or request.form["email"] == "":
                    categories = cursor_to_list(categories_col.find({}), "name")
                    return render_template("report.html",
                                           reportdict=blank_reportdict,
                                           field_error=True,
                                           categories=categories,
                                           admin=check_if_logged(),
                                           redirect_to=redirect_to)

                elif check_profanity(request.form["name"]) or check_profanity(request.form["content"]):
                    categories = cursor_to_list(categories_col.find({}), "name")
                    return render_template("report.html",
                                           reportdict=blank_reportdict,
                                           profanity_found=True,
                                           categories=categories,
                                           admin=check_if_logged(),
                                           redirect_to=redirect_to)

                elif category not in cursor_to_list(categories_col.find({}), "name"):
                    categories = cursor_to_list(categories_col.find({}), "name")
                    return render_template("report.html",
                                           reportdict=blank_reportdict,
                                           field_error=True,
                                           categories=categories,
                                           admin=check_if_logged(),
                                           redirect_to=redirect_to)
                
                elif not valid_email(request.form["email"]):
                    categories = cursor_to_list(categories_col.find({}), "name")
                    return render_template("report.html",
                                            reportdict=blank_reportdict,
                                            email_error=True,
                                            categories=categories,
                                            admin=check_if_logged(),
                                            redirect_to=redirect_to)

                else:

                    edit_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    reports_col.update_one({"id": reportid}, {
                        "$set": {
                            "category": request.form["category"],
                            "name": all_lowercase(request.form["name"]),
                            "content": request.form["content"],
                            "email": request.form["email"],
                            "edittime": edit_time
                        }
                    })

                    result = cursor_to_list(reports_col.find({"id": reportid}))
                    if len(result) != 1:
                        abort(404)

                    return redirect(url_for("show_report", reportid=reportid))

            else:

                categories = cursor_to_list(categories_col.find(), "name")

                result = cursor_to_list(reports_col.find({"id": reportid}))
                if len(result) != 1:
                    abort(404)

                return render_template("edit_report.html",
                                       categories=categories,
                                       reportdict=result[0],
                                       admin=check_if_logged(),
                                       redirect_to=redirect_to)


@app.route("/report", methods=["GET", "POST"])
def report():

    redirect_to = url64.encode(request.url)

    if request.method == "POST":

        try:
            category = request.form["category"]
        except werkzeug.exceptions.BadRequestKeyError:
            category = ""

        if category == ""\
         or request.form["name"] == ""\
         or request.form["content"] == ""\
         or request.form["email"] == "":
            categories = cursor_to_list(categories_col.find({}), "name")
            return render_template("report.html",
                                   reportdict=blank_reportdict,
                                   categories=categories,
                                   field_error=True,
                                   admin=check_if_logged(),
                                   redirect_to=redirect_to)

        elif check_profanity(request.form["name"]) or check_profanity(request.form["content"]):
            categories = cursor_to_list(categories_col.find({}), "name")
            return render_template("report.html",
                                   reportdict=blank_reportdict,
                                   profanity_found=True,
                                   categories=categories,
                                   admin=check_if_logged(),
                                   redirect_to=redirect_to)

        elif category not in cursor_to_list(categories_col.find({}), "name"):
            categories = cursor_to_list(categories_col.find({}), "name")
            return render_template("report.html",
                                   reportdict=blank_reportdict,
                                   field_error=True,
                                   categories=categories,
                                   admin=check_if_logged(),
                                   redirect_to=redirect_to)

        elif not valid_email(request.form["email"]):
            categories = cursor_to_list(categories_col.find({}), "name")
            return render_template("report.html",
                                   reportdict=blank_reportdict,
                                   email_error=True,
                                   categories=categories,
                                   admin=check_if_logged(),
                                   redirect_to=redirect_to)

        else:

            insert_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            ids = cursor_to_list(reports_col.find(), "id")
            report_id = generate_id(ids)

            reports_col.insert_one({
                "id": report_id,
                "inserttime": insert_time,
                "edittime": insert_time,
                "category": request.form["category"],
                "name": all_lowercase(request.form["name"]),
                "content": request.form["content"],
                "email": request.form["email"],
                "verified": False
            })

            categories = cursor_to_list(categories_col.find(), "name")

            return redirect(url_for("show_report", reportid=report_id))

    elif request.method == "GET":

        reportdict = request_args_to_dict({"category": "", "name": "", "content": "", "email": ""})

        categories = cursor_to_list(categories_col.find(), "name")
        return render_template("report.html", categories=categories, admin=check_if_logged(), reportdict=reportdict, redirect_to=redirect_to)


@app.route("/login", methods=["GET", "POST"])
def login():

    try:
        redirect_to = request.args["redirect"]
    except KeyError: # werkzeug.exceptions.BadRequestKeyError:
        redirect_to = ""
    
    try:
        redirect_to_decoded = url64.decode(redirect_to)
    except:
        redirect_to_decoded = url_for("index")
    else:
        if redirect_to_decoded == "":
            redirect_to_decoded = url_for("index")

    if request.method == "POST":

        try:
            request.form["login"]
            request.form["password"]
        except werkzeug.exceptions.BadRequestKeyError:
            return render_template("login.html", field_error=True, admin=check_if_logged(), redirect_to=redirect_to)

        if request.form["login"] == "" or request.form["password"] == "":
            return render_template("login.html", field_error=True, admin=check_if_logged(), redirect_to=redirect_to)
        else:

            username = request.form["login"]
            password = request.form["password"]

            result = cursor_to_list(admins_col.find({"login": username}))

            for j in result:
                if check_hashed_psw(password, j["password"]):
                    session["logged"] = True
                    return redirect(redirect_to_decoded)

            return render_template("login.html", data_error=True, admin=check_if_logged(), redirect_to=redirect_to)

    else:
        if check_if_logged():
            return redirect(redirect_to_decoded)
        else:
            return render_template("login.html", admin=check_if_logged(), redirect_to=redirect_to)


@app.route("/logout")
def logout():
    try:
        redirect_to = request.args["redirect"]
    except KeyError: # werkzeug.exceptions.BadRequestKeyError:
        redirect_to = ""
    
    try:
        redirect_to_decoded = url64.decode(redirect_to)
    except:
        redirect_to_decoded = url_for("index")
    else:
        if redirect_to_decoded == "":
            redirect_to_decoded = url_for("index")
    
    if check_if_logged():
        session.pop("logged", None)
        return redirect(redirect_to_decoded)
    else:
        return redirect(url_for("login", redirect_to=redirect_to))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port="8000", debug=DEBUG)
