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
        return render_template("error.html", error_code="404", error_name="Nie znaleziono", error_desc="Niestety, nie istnieje strona, której szukasz. Sprawdź poprawność adresu URL.", admin=check_if_logged(), redirect_to=redirect_to)

@app.errorhandler(500)
def error_500(e):
    redirect_to = url64.encode(request.url)
    if request.url.startswith(API_ENTRYPOINT):
        return jsonify({
            "error": "500 Internal Server Error",
            "description": "Error in server code - please contact service admin."
        }), 500
    else:
        return render_template("error.html", error_code="500", error_name="Wewnętrzny Błąd Serwera", error_desc="Jest błąd w kodzie serwera. Powiadom administratora strony.", admin=check_if_logged(), redirect_to=redirect_to)

@app.route("/")
def index():
    redirect_to = url64.encode(request.url)
    return render_template("index.html", admin=check_if_logged(), redirect_to=redirect_to)

@app.route("/ranking")
def ranking():
    redirect_to = url64.encode(request.url)
    
    reports = reports_col.find({"verified": True})

    count = {}
    for reportdict in reports:
        try:
            count[reportdict["name"]] += 1
        except KeyError:
            count[reportdict["name"]] = 1
    
    result = rank(count)

    return render_template("ranking.html", ranking_reports=result, admin=check_if_logged(), redirect_to=redirect_to)


@app.route("/browse")
def browse():
    redirect_to = url64.encode(request.url)

    categories = cursor_to_list(categories_col.find({"accepted": True}))
    cat_map = {}
    for x in categories:
        cat_map[x["id"]] = x["name"]

    query = {}
    fields = {"name": "", "category_id": "", "category_name": "", "verified": ""}

    try:
        request.args["name"]
    except KeyError:
        pass
    else:
        query["name"] = {"$regex": request.args["name"].lower()}
        fields["name"] = request.args["name"].lower()

    try:
        request.args["category"]
    except KeyError:
        pass
    else:
        if request.args["category"] in cat_map.keys():
            query["category"] = request.args["category"]
            fields["category_id"] = request.args["category"]
            fields["category_name"] = cursor_to_list(categories_col.find({"id": request.args["category"]}), "name")[0]
    
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
    for i in range(len(elements)):
        elements[i]["category"] = cat_map[elements[i]["category"]]

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

    cat_result = cursor_to_list(categories_col.find({"id": result[0]["category"]}))
    if len(cat_result) != 1:
        abort(500)
    category_name = cat_result[0]["name"]

    return render_template("show_report.html", reportdict=result[0], admin=check_if_logged(), category_name=category_name, redirect_to=redirect_to)


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
                
                categories = cursor_to_list(categories_col.find({"accepted": True}))
                cat_map = {}
                for x in categories:
                    cat_map[x["name"]] = x["id"]
                categories = cursor_to_list(categories, "name")

                if category == "" \
                 or request.form["name"] == "" \
                 or request.form["content"] == "" \
                 or request.form["email"] == "":
                    return render_template("report.html",
                                           reportdict=blank_reportdict,
                                           field_error=True,
                                           categories=categories,
                                           admin=check_if_logged(),
                                           redirect_to=redirect_to)

                elif check_profanity(request.form["content"]):
                    return render_template("report.html",
                                           reportdict=blank_reportdict,
                                           profanity_found=True,
                                           categories=categories,
                                           admin=check_if_logged(),
                                           redirect_to=redirect_to)

                elif category not in categories:
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
                            "category": cat_map[request.form["category"]],
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

                categories = cursor_to_list(categories_col.find({"accepted": True}), "name")

                result = cursor_to_list(reports_col.find({"id": reportid}))
                if len(result) != 1:
                    abort(404)
                
                cat_result = cursor_to_list(categories_col.find({"id": result[0]["category"]}))
                if len(cat_result) != 1:
                    abort(500)
                result[0]["category"] = cat_result[0]["name"]

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

        categories = cursor_to_list(categories_col.find({"accepted": True}))
        cat_map = {}
        for x in categories:
            cat_map[x["name"]] = x["id"]
        categories = cursor_to_list(categories, "name")

        if category == ""\
         or request.form["name"] == ""\
         or request.form["content"] == ""\
         or request.form["email"] == "":
            return render_template("report.html",
                                   reportdict=blank_reportdict,
                                   categories=categories,
                                   field_error=True,
                                   admin=check_if_logged(),
                                   redirect_to=redirect_to)

        elif check_profanity(request.form["content"]):
            return render_template("report.html",
                                   reportdict=blank_reportdict,
                                   profanity_found=True,
                                   categories=categories,
                                   admin=check_if_logged(),
                                   redirect_to=redirect_to)

        elif category not in categories:
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
                "category": cat_map[request.form["category"]],
                "name": all_lowercase(request.form["name"]),
                "content": request.form["content"],
                "email": request.form["email"],
                "verified": False
            })

            categories = cursor_to_list(categories_col.find({"accepted": True}), "name")

            return redirect(url_for("show_report", reportid=report_id))

    elif request.method == "GET":

        reportdict = request_args_to_dict({"category": "", "name": "", "content": "", "email": ""})

        categories = cursor_to_list(categories_col.find({"accepted": True}))
        cat_map = {"": ""}
        for x in categories:
            cat_map[x["id"]] = x["name"]
        categories = cursor_to_list(categories, "name")

        reportdict["category"] = cat_map[reportdict["category"]]

        return render_template("report.html", categories=categories, admin=check_if_logged(), reportdict=reportdict, redirect_to=redirect_to)


@app.route("/login", methods=["GET", "POST"])
def login():

    try:
        redirect_to = request.args["redirect"]
    except KeyError:
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


@app.route("/suggestcategory", methods=["GET", "POST"])
def suggest_category():

    redirect_to = url64.encode(request.url)

    try:
        request.args["embed"]
    except KeyError:
        embed = False
    else:
        if request.args["embed"] == "true":
            embed = True
        else:
            embed = False

    if embed == True:
        if request.method == "POST":
            try:
                request.form["name"]
            except KeyError:
                return render_template("suggest_category_embed.html", field_error=True, admin=check_if_logged())
            else:
                category_name = request.form["name"].lower()
            
            if check_profanity(category_name):
                return render_template("suggest_category_embed.html", profanity_error=True, admin=check_if_logged())
            elif category_name in cursor_to_list(categories_col.find(), "name"):
                return render_template("suggest_category_embed.html", already_reported_error=True, admin=check_if_logged())
            elif category_name == "":
                return render_template("suggest_category_embed.html", field_error=True, admin=check_if_logged())
            
            categories_col.insert_one({
                "id": generate_id(cursor_to_list(categories_col.find({}), "id")),
                "name": category_name,
                "accepted": check_if_logged()
            })

            return_str = "close"
            if check_if_logged():
                return_str += " "
                return_str += category_name
            return return_str

        elif request.method == "GET":
            
            if embed:
                return render_template("suggest_category_embed.html", admin=check_if_logged())
            else:
                redirect_to = url64.encode(request.url)
                return render_template("suggest_category.html", admin=check_if_logged(), redirect_to=redirect_to)
    else:
        return render_template("suggest_category.html", admin=check_if_logged(), redirect_to=redirect_to)


@app.route("/admin")
def admin_panel():
    redirect_to = url64.encode(request.url)
    if check_if_logged():
        return render_template("admin_panel.html", admin=True, redirect_to=redirect_to)
    else:
        return redirect(url_for("login", redirect=redirect_to))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port="8000", debug=DEBUG)
