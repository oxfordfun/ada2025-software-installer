import logging
import webbrowser
import string
import threading
import secrets
import flask
from cachetools import cached, TTLCache
import os
import requests
import subprocess
from distutils.version import StrictVersion
from shlex import quote
import json
import urllib.request
from rapidfuzz import fuzz

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
DL_PATH = "/home/ubuntu/Downloads/"  # make sure this ends in a "/"
ADA_URL = "https://ada.stfc.ac.uk/software_db"


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
    return flask.render_template(
        "app.jinja2", software_info=software_info, title="Software List"
    )


@app.route("/ubuntu_packages")
def ubuntu_packages():
    """
    Only lists ubuntu packages
    """
    software_info = get_ubuntu_packages()
    return flask.render_template(
        "app.jinja2", software_info=software_info, title="Ubuntu Packages"
    )


@app.route("/apptainer_software")
def apptainer_software():
    """
    Only lists software that are apptainers
    """
    software_info = get_apptainer_software()
    return flask.render_template(
        "app.jinja2", software_info=software_info, title="Apptainer Software"
    )


@app.route("/search")
def search():
    """
    Search page. Lists all software matching a search term.
    """
    search_term = flask.request.args["search"]
    if len(search_term) == 0:
        return flask.redirect("/")
    software_info = get_searched_software_info(search_term)
    return flask.render_template(
        "app.jinja2",
        software_info=software_info,
        title="Search Results",
        search_term=search_term,
    )


@app.route("/versions/<software_name>")
def versions(software_name):
    """
    Software versions page. List all available versions of a software.
    """
    if (not software_name) or (software_name not in get_software_list()):
        return flask.redirect(flask.url_for("index"))
    all_versions = get_all_versions_of_software(software_name)
    return flask.render_template(
        "versions.jinja2",
        software_name=software_name,
        all_versions=all_versions,
        title=software_name + " Versions",
    )


@app.route("/download/<software_name>/<software_version>")
def download(software_name, software_version):
    """
    Download a specific piece of software
    """
    software_file = get_software_file()

    name_count = 0
    for name in software_file:
        if software_file[name_count]["name"] == software_name:
            version_count = 0
            for version in software_file[name_count]["variants"]:
                if (
                    software_file[name_count]["variants"][version_count]["version"]
                    == software_version
                ):
                    if software_file[name_count]["type"] == "apptainer":
                        apptainer_file = software_file[name_count]["variants"][
                            version_count
                        ]["apptainer_file"]
                    desktop_file = software_file[name_count]["variants"][version_count][
                        "desktop_file"
                    ]
                    icon_file = software_file[name_count]["variants"][version_count][
                        "icon_file"
                    ]
                version_count += 1
            software_type = software_file[name_count]["type"]
        name_count += 1

    if software_type == "apptainer":
        logging.info(f"Downloading {software_name} {software_version}")

        # get software
        path = f"{DL_PATH}{software_name.lower()}_{software_version}.sif"
        cmd = f"wget -O {path} {apptainer_file} && chmod +x {path}"
        threading.Thread(target=run_term_cmd, args=(cmd,)).start()
        flask.flash(
            f"{software_name} {software_version} is being downloaded to {path}. Please allow some time for this download to complete."
        )
    elif software_type == "apt":
        logging.info(f"Downloading {software_name}")
        flask.flash(
            f"{software_name} is being downloaded. Please allow some time for this download to complete."
        )

        # Install software
        cmd = f"sudo apt -y install {software_name.lower()}"
        threading.Thread(target=run_term_cmd, args=(cmd,)).start()

    # get desktop item
    path = f"/home/ubuntu/Desktop/{software_name.lower()}_{software_version}.desktop"
    cmd = f"wget -O {path} {desktop_file} && chmod +x {path} && chown ubuntu {path}"
    threading.Thread(target=run_term_cmd, args=(cmd,)).start()

    # get icon
    path = f"/usr/share/pixmaps/{software_name.lower()}_icon.png"
    cmd = f"sudo wget -O {path} {icon_file}"
    logging.info(cmd)
    threading.Thread(target=run_term_cmd, args=(cmd,)).start()

    return flask.redirect(flask.url_for("index"))


@cached(cache=TTLCache(maxsize=1, ttl=60))
def get_software_info():
    """
    Get list of software info
    """
    logging.info(f"Getting info for all available software.")
    software_list = get_software_list()
    version_list = get_all_latest_software_versions(software_list)
    description_list = get_software_description(software_list)
    software_info = []
    for i in range(0, len(software_list)):
        software_info.append(
            [
                software_list[i],
                version_list[i],
                software_list[i].lower(),
                description_list[i],
            ]
        )
    return software_info


@cached(cache=TTLCache(maxsize=1, ttl=60))
def get_ubuntu_packages():
    """
    Get list of ubuntu packages
    """
    ubuntu_packages = []
    software_list = get_software_file()
    name_count = 0

    for software in software_list:
        if software_list[name_count]["type"] == "apt":
            ubuntu_packages.append(software_list[name_count]["name"])
        name_count += 1

    version_list = get_all_latest_software_versions(ubuntu_packages)
    description_list = get_software_description(ubuntu_packages)
    software_list = []

    for i in range(0, len(ubuntu_packages)):
        software_list.append(
            [
                ubuntu_packages[i],
                version_list[i],
                ubuntu_packages[i].lower(),
                description_list[i],
            ]
        )

    return software_list


@cached(cache=TTLCache(maxsize=1, ttl=60))
def get_apptainer_software():
    """
    Get list of apptainer software
    """
    apptainer_software = []
    software_list = get_software_file()
    name_count = 0

    for software in software_list:
        if software_list[name_count]["type"] == "apptainer":
            apptainer_software.append(software_list[name_count]["name"])
        name_count += 1

    version_list = get_all_latest_software_versions(apptainer_software)
    description_list = get_software_description(apptainer_software)
    software_list = []

    for i in range(0, len(apptainer_software)):
        software_list.append(
            [
                apptainer_software[i],
                version_list[i],
                apptainer_software[i].lower(),
                description_list[i],
            ]
        )

    return software_list


def get_searched_software_info(search_term):
    """
    Get list of searched for software info
    """
    logging.info(f"Getting software info for searched software.")
    full_software_list = get_software_list()
    software_list = find_items_with_string(full_software_list, search_term)
    version_list = get_all_latest_software_versions(software_list)
    description_list = get_software_description(software_list)
    software_info = []
    if len(software_list) == 0:
        flask.flash("No results found", "danger")
    else:
        for i in range(0, len(software_list)):
            if version_list[i]:
                software_info.append(
                    [
                        software_list[i],
                        version_list[i],
                        software_list[i].lower(),
                        description_list[i],
                    ]
                )
    return software_info


def find_items_with_string(arr, search_string):
    """
    Find items in a list that contain a search string
    """
    result = []
    for item in arr:
        if fuzz.partial_ratio(search_string.lower(), item.lower()) > 50:
            result.append(item)
    return result


def get_software_list():
    """
    Get list of all available software names
    """
    logging.info(f"Retrieving software list")
    softwares = []
    software_list = get_software_file()
    count = 0
    for software_name in software_list:
        softwares.append(software_list[count]["name"])
        count += 1

    return softwares


def get_software_description(software_list):
    """
    Get a list of the descriptions of all software
    """
    logging.info(f"Retrieving software descriptions")
    descriptions = []
    software_file = get_software_file()
    name_count = 0
    for software_description in software_file:
        if software_file[name_count]["name"] in software_list:
            descriptions.append(software_file[name_count]["description"])
        name_count += 1

    return descriptions


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
    versions = get_all_versions_of_software(software_name)

    if not versions:
        return ""

    try:
        return max(versions, key=StrictVersion)
    except:
        return max(versions)


def get_all_versions_of_software(software):
    """
    Get all available versions of a specific piece of software
    """
    logging.info(f"Getting list of all available versions of {software}")
    versions = []
    software_list = get_software_file()
    name_count = 0
    version_count = 0
    for software_name in software_list:
        if software_list[name_count]["name"] == software:
            software_versions = software_list[name_count]["variants"]
            for software_version in software_versions:
                versions.append(
                    software_list[name_count]["variants"][version_count]["version"]
                )
                version_count += 1
        name_count += 1
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
    """
    Get software file from Ada endpoint, or file if endpoint is unavailable, and return as a dictionary
    """
    try:
        file = open("./software_db.txt", "w")
        with urllib.request.urlopen(ADA_URL) as url:
            software = json.load(url)
        file.write(json.dumps(software, indent=4))
        file.close()
        return software
    except:
        file = open("./software_db.txt", "r")
        software = file.read()
        return json.loads(software)


def write_software_file():
    """
    Write the contents of the Software database, from Ada, to a file, this is to be used as a backup incase the url cannot be accessed later
    """
    file = open("./software_db.txt", "w")
    with urllib.request.urlopen(ADA_URL) as url:
        software = json.load(url)
    file.write(json.dumps(software, indent=4))
    file.close()


write_software_file()


def main():
    app.run(host=HOST, port=PORT, debug=DEBUG)


if __name__ == "__main__":
    webbrowser.open_new_tab(f"http://{HOST}:{str(PORT)}/")
    main()
