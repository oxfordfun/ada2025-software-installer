import logging
import webbrowser
import string
import threading
import secrets
import flask
import os
import requests
import subprocess
from bs4 import BeautifulSoup
from distutils.version import StrictVersion
from shlex import quote
import json

logging.basicConfig(
    level=logging.DEBUG,
    datefmt="%Y-%m-%d/%H:%M:%S",
    format="%(asctime)s %(message)s",
)

def str_to_bool(str):
    if str == "True":
        return True
    return False


HOST = os.getenv("ADA2025_SI_HOST") or "127.0.0.1"
PORT = os.getenv("ADA2025_SI_PORT") or 7322
DEBUG = str_to_bool(os.getenv("ADA2025_SI_DEBUG"))
FS_URL = (
    os.getenv("ADA2025_SI_FS_URL")
    or "https://ada-files.oxfordfun.com/software/containers/"
)  # make sure this ends in a "/"
DL_PATH = (
    os.getenv("ADA2025_SI_DL_PATH") or "/home/ubuntu/Downloads/"
)  # make sure this ends in a "/"


def gen_token(length):
    """
    Generate a cryptographically secure alphanumeric string of the given length.
    """
    alphabet = string.ascii_letters + string.digits
    secure_string = "".join(secrets.choice(alphabet) for _ in range(length))
    return secure_string


app = flask.Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("ADA2025_SI_FLASK_SECRET_KEY") or gen_token(
    32
)


@app.route("/")
def index():
    """
    Home page. Lists all available software to the user.
    """
    software_info = get_software_info()
    return flask.render_template("app.jinja2", software_info=software_info)


@app.route("/search")
def search():
    """
    Search page. Lists all software matching a search term.
    """
    search_term = flask.request.args["search"]
    software_info = get_software_info(search_term)
    return flask.render_template("app.jinja2", software_info=software_info)


@app.route("/versions/<software_name>")
def versions(software_name):
    """
    Software versions page. List all available versions of a software.
    """
    if (not software_name) or (software_name not in get_software_list()):
        return flask.redirect(flask.url_for("index"))
    all_versions = get_all_versions_of_software(software_name)
    prefix = software_name + "-"
    all_versions = [
        version[len(prefix) :] for version in all_versions if version.startswith(prefix)
    ]
    return flask.render_template(
        "versions.jinja2", software_name=software_name, all_versions=all_versions
    )


@app.route("/download/<software_name>/<software_version>")
def download(software_name, software_version):
    """
    Download a specific piece of software
    """
    logging.info(f"Downloading {software_name} {software_version}")
    source_url = flask.request.args.get("source_url") or "index"

    # get software
    url = (
        FS_URL
        + software_name
        + f"/{software_name}-{software_version}/{software_name.lower()}_latest.sif"
    )
    path = f"{DL_PATH}{software_name.lower()}_{software_version}.sif"
    cmd = f"wget -O {path} {url} && chmod +x {path}"
    threading.Thread(target=run_term_cmd, args=(cmd,)).start()
    flask.flash(
        f"{software_name} {software_version} is being downloaded to {path}. Please allow for some time for this download to complete."
    )

    # get desktop item
    url = FS_URL + software_name + f"/{software_name}-{software_version}/{software_name.lower()}_{software_version}.desktop"
    path = f"/home/ubuntu/Desktop/{software_name.lower()}_{software_version}.desktop"
    cmd = f"wget -O {path} {url} && chmod +x {path}"
    threading.Thread(target=run_term_cmd, args=(cmd,)).start()

    # get icon
    url = FS_URL + software_name + f"/{software_name}-{software_version}/{software_name.lower()}_icon.png"
    path = f"/usr/share/pixmaps/{software_name.lower()}_icon.png"
    cmd = f"sudo wget -O {path} {url}"
    logging.info(cmd)
    threading.Thread(target=run_term_cmd, args=(cmd,)).start()

    if source_url == "versions":
        return flask.redirect(flask.url_for(source_url, software_name=software_name))
    else:
        return flask.redirect(flask.url_for(source_url))


def get_software_info(search_term=None):
    """
    Get list of software names and available versions for each of them. Can take a search term to filter.
    """
    logging.info(f"Getting info for all available software.")
    software_list = get_software_list()
    if search_term:
        software_list = find_items_with_string(software_list, search_term)
    version_list = get_all_latest_software_versions(software_list)
    software_info = []
    for i in range(0, len(software_list)):
        if version_list[i]:
            software_info.append([software_list[i], version_list[i]])
    return software_info


def find_items_with_string(arr, search_string):
    """
    Find items in a list that contain a search string
    """
    result = []
    for item in arr:
        if search_string in item:
            result.append(item)
    return result


def get_software_list():
    """
    Get list of all available software names
    """
    logging.info(f"Retrieving software list from {FS_URL}")
    response = requests.get(FS_URL)
    softwares = []
    if response.status_code == 200:
        software_list = get_software_file()
        i = 0
        for software_name in software_list:
            softwares.append(software_list["contents"][i]["name"])
            i+=1
        
    else:
        logging.error(f"Error: Unable to retrieve content from {FS_URL}")
    return softwares


def get_all_latest_software_versions(software_list):
    """
    Get the latest version available for a list of software names
    """
    logging.info("Determining latest versions for each piece of software")
    latest_versions = []
    for software in software_list:
        latest_versions.append(get_latest_software_version(software))
    return latest_versions


def get_latest_software_version(software_name):
    """
    Get the latest available version for a specific piece of software
    """
    logging.info(f"Getting latest software version for {software_name}")
    all_versions = get_all_versions_of_software(software_name)

    prefix = software_name + "-"
    filtered_versions = [
        version[len(prefix) :] for version in all_versions if version.startswith(prefix)
    ]

    if not filtered_versions:
        return ""

    try:
        return max(filtered_versions, key=StrictVersion)
    except:
        return max(filtered_versions)


def get_all_versions_of_software(software):
    """
    Get all available versions of a specific piece of software
    """
    logging.info(f"Getting list of all available versions of {software}")
    versions = []
    response = requests.get(FS_URL + f"/{software}")
    if response.status_code == 200:
        software_list = get_software_file()
        i = 0
        x = 0
        for software_name in software_list:
            if software_list["contents"][i]["name"] == software:
                software_versions = software_list["contents"][i]["contents"]
                for software_version in software_versions:
                    versions.append(software_list["contents"][i]["contents"][x]["name"])
                    x+=1
            i+=1
    return versions


def run_term_cmd(cmd):
    """
    Run a bash command in terminal
    """
    term_cmd = f"sudo bash -c {quote(cmd)}"
    logging.info(term_cmd)
    try:
        result = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True
        )
        logging.info(result.stdout)
        logging.info(result.stderr)
    except subprocess.CalledProcessError as e:
        logging.exception("Command execution failed:", e)


def get_software_file():
    software = requests.get("https://ada-files.oxfordfun.com/software/containers/software.json")
    return software.json()


def main():
    app.run(host=HOST, port=PORT, debug=DEBUG)


if __name__ == "__main__":
    webbrowser.open_new_tab(f"http://{HOST}:{str(PORT)}/")
    main()
