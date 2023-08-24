import logging
import webbrowser
import flask
import os
import requests
from bs4 import  BeautifulSoup

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
    software_list = get_software_list()
    return flask.render_template("app.jinja2", software_list=software_list)

@app.route("/search")
def search():
    software_list = get_software_list()
    search_term = flask.request.args["search"]
    if search_term:
        software_list = find_items_with_string(software_list, search_term)
    return flask.render_template("app.jinja2", software_list=software_list)

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
        soup = BeautifulSoup(response.content, 'html.parser')
        for link in soup.find_all('a'):
            href = link.get('href')
            if href.endswith('/'):
                softwares.append(href)
        softwares.remove("misc/")
        softwares = softwares[1:]
    else:
        print(f"Error: Unable to retrieve content from {FS_URL}")
    return softwares

def main():
    app.run(host=HOST, port=PORT, debug=DEBUG)

if __name__=="__main__":
    main()