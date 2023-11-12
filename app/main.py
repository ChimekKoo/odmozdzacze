from flask import Flask, render_template, request, redirect, url_for, abort, session, make_response
from datetime import datetime
import werkzeug
import url64
from urllib.parse import urlparse
from os import environ
import random
import string
from dotenv import load_dotenv

from constants import *
from utils import *
from db import reports_col, categories_col, admins_col

load_dotenv()

app = Flask(__name__)

app.secret_key = "".join(random.choice(string.ascii_lowercase+string.ascii_uppercase+string.digits) for _ in range(64))
app.debug = environ.get("ODMOZDZACZE_DEBUG", False).lower() == "true"

@app.errorhandler(404)
def error_404(e):
    return render_template("error.html", error_code="404", error_name="Nie znaleziono", error_desc="Niestety, nie istnieje strona, której szukasz. Sprawdź poprawność adresu URL.")

@app.errorhandler(500)
def error_500(e):
    return render_template("error.html", error_code="500", error_name="Wewnętrzny Błąd Serwera", error_desc="Jest błąd w kodzie serwera. Proszę, skontaktuj się ze mną w zakładce Kontakt i opisz w jaki sposób zostałeś tu przekierowany")

@app.context_processor
def inject():
    return dict(
        admin=is_logged(),
        redirect_to=url64.encode(request.url),
        banners=get_banners(),
    )

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/ranking")
def ranking():

    reports = reports_col.find({"verified": True})

    count = {}
    for reportdict in reports:
        try:
            count[reportdict["name"]] += 1
        except KeyError:
            count[reportdict["name"]] = 1
    
    result = rank(count)

    return render_template("ranking.html", ranking_reports=result)


@app.route("/browse")
def browse():

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
        if not is_logged():
            query["verified"] = True
            fields["verified"] = True
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

    return render_template("browse.html", elements=elements, fields=fields, categories=categories)


@app.route("/developer")
def developer():
    return render_template("developer.html")

@app.route("/showreport/<reportid>")
def show_report(reportid):
    
    if reports_col.count_documents({"id": reportid}) == 0:
        abort(404)
    
    reportdict = reports_col.find_one({"id": reportid})
    category_name = categories_col.find_one({"id": reportdict["category"]})["name"]

    wait_for_verify = not is_logged() and not reportdict["verified"] and request.args.get("justreported") == "true"

    return render_template("show_report.html", reportdict=reportdict, category_name=category_name, wait_for_verify=wait_for_verify)


@app.route("/admin/verifyreport/<reportid>")
def verify_report(reportid):
    result = cursor_to_list(reports_col.find({"id": reportid}))
    if len(result) != 1:
        abort(404)
    else:
        if is_logged():
            reports_col.update_one({"id": reportid}, {"$set": {
                "verified": True
            }})
            return redirect(url_for("show_report", reportid=reportid))
        else:
            return redirect(url_for("login"))


@app.route("/admin/unverifyreport/<reportid>")
def unverify_report(reportid):
    result = cursor_to_list(reports_col.find({"id": reportid}))
    if len(result) != 1:
        abort(404)
    else:
        if is_logged():
            reports_col.update_one({"id": reportid}, {"$set": {
                "verified": False
            }})
            return redirect(url_for("show_report", reportid=reportid))
        else:
            return redirect(url_for("login"))


@app.route("/admin/deletereport/<reportid>")
def delete_report(reportid):

    result = cursor_to_list(reports_col.find({"id": reportid}))
    if len(result) != 1:
        abort(404)
    else:
        if is_logged():
            reports_col.delete_one({"id": reportid})
            return redirect(url_for("browse"))
        else:
            return redirect(url_for("login"))


@app.route("/admin/editreport/<reportid>", methods=["GET", "POST"])
def edit_report(reportid):
    
    if reports_col.count_documents({"id": reportid}) == 0:
        abort(404)

    if not is_logged():
        return redirect(url_for("login"))

    if request.method == "POST":

        categories = cursor_to_list(categories_col.find({"accepted": True}), "name")        

        reportdict = {
            "id": reportid,
            "name": request.form.get("name", "").lower(),
            "content": request.form.get("content", ""),
            "email": request.form.get("email", ""),
            "category": request.form.get("category", ""),
        }

        field_error = False
        profanity_found = False
        email_error = False

        if reportdict["category"] == ""\
         or reportdict["name"] == ""\
         or reportdict["content"] == ""\
         or reportdict["email"] == "":
            field_error = True
        
        if categories_col.count_documents({"name": reportdict["category"]}) == 0:
            field_error = True

        if check_profanity(reportdict["name"]) or check_profanity(reportdict["content"]):
            profanity_found = True
        
        if not valid_email(reportdict["email"]):
            email_error = True
        
        if field_error or profanity_found or email_error:
            return render_template(
                "edit_report.html",
                categories=categories,
                reportdict=reportdict,
                field_error=field_error,
                profanity_found=profanity_found,
                email_error=email_error,
            )
        else:
            edit_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            category_id = categories_col.find_one({"name": reportdict["category"]})["id"]

            reports_col.update_one({"id": reportid}, {
                "$set": {
                    "category": category_id,
                    "name": reportdict["name"],
                    "content": reportdict["content"],
                    "email": reportdict["email"],
                    "edittime": edit_time
                }
            })
            
            if reports_col.count_documents({"id": reportid}) == 0:
                abort(404)

            return redirect(url_for("show_report", reportid=reportid))

    elif request.method == "GET":

        categories = cursor_to_list(categories_col.find({"accepted": True}), "name")
        
        if reports_col.count_documents({"id": reportid}) == 0:
            abort(404)
        
        reportdict = reports_col.find_one({"id": reportid})
        reportdict["category"] = categories_col.find_one({"id": reportdict["category"]})["name"]

        return render_template("edit_report.html",
                                categories=categories,
                                reportdict=reportdict)


@app.route("/report", methods=["GET", "POST"])
def report():
    recaptcha_site_key = environ.get("ODMOZDZACZE_RECAPTCHA_SITE_KEY")

    if request.method == "POST":

        categories = cursor_to_list(categories_col.find({"accepted": True}), "name")

        reportdict = {
            "name": request.form.get("name", "").lower(),
            "content": request.form.get("content", ""),
            "email": request.form.get("email", ""),
            "category": request.form.get("category", ""),
        }

        field_error = False
        profanity_found = False
        email_error = False
        recaptcha_error = False

        if reportdict["category"] == ""\
         or reportdict["name"] == ""\
         or reportdict["content"] == ""\
         or reportdict["email"] == "":
            field_error = True

        if check_profanity(reportdict["name"]) or check_profanity(reportdict["content"]):
            profanity_found = True

        if categories_col.count_documents({"name": reportdict["category"]}) == 0:
            field_error = True

        if not valid_email(reportdict["email"]):
            email_error = True
            
        if not is_human(request.form.get("g-recaptcha-response"), environ.get("ODMOZDZACZE_RECAPTCHA_SECRET_KEY")):
            recaptcha_error = True
        
        if field_error or profanity_found or email_error or recaptcha_error:
            return render_template(
                "report.html",
                categories=categories,
                field_error=field_error,
                profanity_found=profanity_found,
                email_error=email_error,
                recaptcha_error=recaptcha_error,
                recaptcha_sitekey=recaptcha_site_key,
                reportdict=reportdict,
                error=True
            )
        else:
            insert_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            ids = cursor_to_list(reports_col.find(), "id")
            report_id = generate_id(ids)

            category_id = categories_col.find_one({"name": reportdict["category"]})["id"]

            reports_col.insert_one({
                "id": report_id,
                "inserttime": insert_time,
                "edittime": insert_time,
                "category": category_id,
                "name": reportdict["name"],
                "content": reportdict["content"],
                "email": reportdict["email"],
                "verified": False
            })

            return redirect(url_for("show_report", reportid=report_id, justreported="true"))

    elif request.method == "GET":

        category_id = request.args.get("category", "")

        reportdict = {
            "category": "",
            "name": request.args.get("name", ""),
            "content": request.args.get("content", ""),
            "email": request.args.get("email", "")
        }

        if categories_col.count_documents({"id": category_id, "accepted": True}) > 0:
            reportdict["category"] = categories_col.find_one({"id": category_id})["name"]

        categories = cursor_to_list(categories_col.find({"accepted": True}), "name")

        return render_template("report.html", categories=categories, reportdict=reportdict, recaptcha_sitekey=recaptcha_site_key)


@app.route("/login", methods=["GET", "POST"])
def login():
    redirect_to = request.args.get("redirect", "")
    
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
            return render_template("login.html", field_error=True)

        if request.form["login"] == "" or request.form["password"] == "":
            return render_template("login.html", field_error=True)
        else:

            username = request.form["login"]
            password = request.form["password"]

            result = admins_col.find_one({"login": username})

            if check_hashed_psw(password, result["password"]):
                session["login"] = username
                return redirect(redirect_to_decoded)

            return render_template("login.html", data_error=True)

    else:
        if is_logged():
            return redirect(redirect_to_decoded)
        else:
            return render_template("login.html")


@app.route("/logout")
def logout():
    redirect_to = request.args.get("redirect", "")
    
    try:
        redirect_to_decoded = url64.decode(redirect_to)
    except:
        redirect_to_decoded = url_for("index")
    else:
        if redirect_to_decoded == "":
            redirect_to_decoded = url_for("index")
    
    if is_logged():
        session.pop("login", None)
        return redirect(redirect_to_decoded)
    else:
        return redirect(url_for("login"))


@app.route("/newcategory", methods=["GET", "POST"])
def suggest_category():

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
                return render_template("suggest_category_embed.html", field_error=True)
            else:
                category_name = request.form["name"].lower()
            
            if check_profanity(category_name):
                return render_template("suggest_category_embed.html", profanity_error=True)
            elif category_name in cursor_to_list(categories_col.find(), "name"):
                return render_template("suggest_category_embed.html", already_reported_error=True)
            elif category_name == "":
                return render_template("suggest_category_embed.html", field_error=True)
            
            categories_col.insert_one({
                "id": generate_id(cursor_to_list(categories_col.find({}), "id")),
                "name": category_name,
                "accepted": is_logged()
            })

            return_str = "close"
            if is_logged():
                return_str += " "
                return_str += category_name
            return return_str

        elif request.method == "GET":
            
            if embed:
                return render_template("suggest_category_embed.html")
            else:
                
                return render_template("suggest_category.html")
    else:
        return render_template("suggest_category.html")


@app.route("/admin")
def admin_panel():
    if is_logged():
        return render_template("admin_panel.html", admin=True)
    else:
        return redirect(url_for("login", redirect=url64.encode(request.url)))

@app.route("/report-guidelines")
def report_guidelines():
    return render_template("report_guidelines.html")

@app.route("/robots.txt")
def robots_txt():
    sitemap_url = url_for("sitemap_xml", _external=True)
    resp = make_response(render_template("robots.txt", sitemap_url=sitemap_url))
    resp.headers["Content-Type"] = "text/plain"
    return resp

@app.route("/sitemap.xml")
def sitemap_xml():
    resp = make_response(render_template("sitemap.xml"))
    resp.headers["Content-Type"] = "application/xml"
    return resp
