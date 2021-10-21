import os
import time
from flask import (
    Flask, 
    Response, 
    render_template,
    make_response, 
    request, 
    url_for, 
    jsonify, 
    redirect,
    flash,
    send_from_directory
)
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

from tasks import celery_app 
from database import (
    create_table_if_not_exists, 
    get_all_records_sort_date,
    delete_record,
)


ALLOWED_EXTENSIONS = ["mov", "mp4", "mkv", "mp3", "acc", "ogg", "m4a", "wav"]
flask_app = Flask("main_app")
flask_app.config['UPLOAD_FOLDER'] = "./uploads/"
flask_app.config['SESSION_TYPE'] = 'filesystem'


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def login_check(f):
    @wraps(f)
    def check(*args, **kwargs):
        auth_hash = request.cookies.get("auth_hash")
        if auth_hash is None:
            return redirect("/login/")
        if check_password_hash(auth_hash, flask_app.config["AUTH_PASS"]) is False:
            return redirect("/login/")
        else:
            return f(*args, **kwargs)

    return check

@flask_app.route("/login/", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        auth_hash = request.cookies.get("auth_hash")
        if auth_hash is not None:
            if check_password_hash(auth_hash, flask_app.config["AUTH_PASS"]) is False:
                return render_template("login.html", status="error")
            else:
                return redirect("/")
        return render_template("login.html")
    if request.method == "POST":
        pwd = generate_password_hash(request.form["pwd"])
        resp = make_response(redirect("/"))
        resp.set_cookie("auth_hash", pwd, max_age=60*60*24*365)
        return resp


@flask_app.route("/favicon.ico")
def favicon():
    return send_from_directory(os.path.join(flask_app.root_path, "static"), "favicon.ico")

@flask_app.route('/download/<path:filename>', methods=['GET', 'POST'])
@login_check
def download(filename):
    directory = os.path.join(flask_app.root_path, 'results')
    return send_from_directory(directory, filename)

@flask_app.route('/try_delete/<path:filename>/<int:id_pk>', methods=['GET', 'POST'])
@login_check
def try_delete(filename, id_pk):
    return render_template("delete.html", filename=filename, id_pk=id_pk)

@flask_app.route('/delete/<int:id_pk>', methods=['GET', 'POST'])
@login_check
def delete(id_pk):
    delete_record(id_pk)
    return redirect("/")

@flask_app.route("/", methods=["GET", "POST"])
@login_check
def index() -> Response:
    if request.method == "GET":
        db_data = get_all_records_sort_date()
        table_data = []
        for rec in db_data:
            row = {
                "id_pk": rec[0],
                "submit_datetime": rec[1].strftime("%Y-%m-%d %H:%M:%S"),
                "name": rec[2],
                "duration": rec[3],
                "status": rec[4],
                "txt_name": os.path.splitext(rec[2])[0] + ".txt",
            }
            table_data.append(row)

        return render_template("index.html", items=table_data)
    if request.method == "POST":
        # check if the post request has the file part
        if 'file' not in request.files:
            print('No file part')
            return redirect(request.url)
        uploaded_file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if uploaded_file.filename == '':
            print('No selected file')
            return redirect(request.url)
        if uploaded_file and allowed_file(uploaded_file.filename):
            filename = secure_filename(uploaded_file.filename)
            save_path = os.path.join(flask_app.config['UPLOAD_FOLDER'], filename)
            uploaded_file.save(save_path)
            print(filename)
            celery_app.send_task("transcribe", args=[save_path, flask_app.config["AZURE_SUB"]])
            time.sleep(1)
            return redirect(request.url)
    return redirect(request.url)


def main():
    flask_app.secret_key = 'super secret key'
    with open("/run/secrets/auth_key") as f:
        auth_key = f.read().strip()
        flask_app.config["AUTH_PASS"] = auth_key
    with open("/run/secrets/azure_key") as f:
        flask_app.config["AZURE_SUB"] = f.read().strip()
    create_table_if_not_exists()

    flask_app.run(host="0.0.0.0", port=5000)


if __name__ == "__main__":
    main()
