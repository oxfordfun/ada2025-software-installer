import logging
import webbrowser
import flask
import os
import requests
from bs4 import BeautifulSoup
from distutils.version import StrictVersion


def str_to_bool(str):
    if str == "True":
        return True
    return False


HOST = os.getenv("ADA2025_SI_HOST") or "127.0.0.1"
PORT = os.getenv("ADA2025_SI_PORT") or 7322
DEBUG = str_to_bool(os.getenv("ADA2025_SI_DEBUG"))
FS_URL = os.getenv("ADA2025_SI_FS_URL") or "https://ada-files.oxfordfun.com/software/"

app = flask.Flask(__name__)


@app.route("/")
def myapp():
    software_info = get_software_info()
    return flask.render_template("app.jinja2", software_info=software_info)


@app.route("/search")
def search():
    search_term = flask.request.args["search"]
    software_info = get_software_info(search_term)
    return flask.render_template("app.jinja2", software_info=software_info)


def get_software_info(search_term=None):
    software_list = get_software_list()
    if search_term:
        software_list = find_items_with_string(software_list, search_term)
    version_list = get_all_latest_software_versions(software_list)
    software_info = []
    for i in range(0, len(software_list)):
        software_info.append([software_list[i], version_list[i]])
    return software_info


def find_items_with_string(arr, search_string):
    result = []
    for item in arr:
        if search_string in item:
            result.append(item)
    return result


def get_software_list():
    response = requests.get(FS_URL)
    softwares = []
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")
        for link in soup.find_all("a"):
            href = link.get("href")
            if href.endswith("/"):
                softwares.append(href[:-1])
        softwares.remove("misc") # remove misc/ TODO: put misc in another directory on file server
        softwares = softwares[1:] # remove ../
    else:
        print(f"Error: Unable to retrieve content from {FS_URL}")
    return softwares


def get_all_latest_software_versions(software_list):
    latest_versions = []
    for software in software_list:
        latest_versions.append(get_latest_software_version(software))
    return latest_versions


def get_latest_software_version(software_name):
    all_versions = get_all_versions_of_software(software_name)

    prefix = software_name + "-"
    filtered_versions = [
        version[len(prefix) :] for version in all_versions if version.startswith(prefix)
    ]

    if not filtered_versions:
        return "None"

    return max(filtered_versions, key=StrictVersion)


def get_all_versions_of_software(software):
    versions = []
    response = requests.get(FS_URL + f"/{software}")
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")
        for link in soup.find_all("a"):
            href = link.get("href")
            if href.endswith("/"):
                versions.append(href[:-1])
    versions = versions[1:] # remove ../
    return versions


def main():
    app.run(host=HOST, port=PORT, debug=DEBUG)


if __name__ == "__main__":
    main()
