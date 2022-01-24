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
    "datetime": "",
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
        return render_template("error.html", error_num="404", error_name="Nie znaleziono", admin=check_if_logged(), redirect_to=redirect_to)


@app.route("/")
def index():
    redirect_to = url64.encode(request.url)
    return render_template("index.html", admin=check_if_logged(), redirect_to=redirect_to)


@app.route("/about")
def about():
    redirect_to = url64.encode(request.url)
    return render_template("about.html", admin=check_if_logged(), redirect_to=redirect_to)


@app.route("/ranking")
def ranking():
    redirect_to = url64.encode(request.url)
    result = cursor_to_list(reports_col.find())

    return render_template("ranking.html", ranking_reports=result, admin=check_if_logged(), redirect_to=redirect_to)


@app.route("/browse")
def browse():
    redirect_to = url64.encode(request.url)

    # request_args = request_args_to_dict({"q": "", "category": "", "per-page": "10", "verified": "on"})
    #
    # if request_args["verified"] == "verified":
    #     request_args["verified"] = True
    # elif request_args["verified"] == "unverified":
    #     request_args["verified"] = False
    # else:
    #     request_args["verified"] = ""
    #
    # request_args["q"] = request_args["q"].lower()
    #
    # elements = cursor_to_list(reports_col.find({
    #     "name": request_args["q"],
    #     "category": request_args["category"],
    #     "verified": request_args["verified"]
    # }))
    #
    # per_page = str(request_args["per-page"])
    #
    # try:
    #     per_page = int(per_page)
    # except ValueError:
    #     per_page = len(elements)
    #
    # if len(elements) > per_page:
    #     elements = elements[:per_page]

    query = {}
    for arg in ["q", "category", "verified", "per-page"]:
        try:
            request.args[arg]
        except KeyError:
            pass
        else:
            if request.args[arg] != "":

                if arg == "per-page":
                    per_page = request.args[arg]
                elif arg == "verified":
                    if request.args[arg] == "verified":
                        query[arg] = True
                    elif request.args[arg] == "unverified":
                        query[arg] = False
                    else:
                        continue
                else:
                    query[arg] = request.args[arg]

    elements = cursor_to_list(reports_col.find(query))

    return render_template("browse.html",
                           elements=elements,
                           categories=cursor_to_list(categories_col.find(), "name"),
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

                    reports_col.update_one({"id": reportid}, {
                        "$set": {
                            "category": request.form["category"],
                            "name": request.form["name"],
                            "content": request.form["content"],
                            "email": request.form["email"]
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
