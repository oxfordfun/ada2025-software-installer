# ada2025-software-installer
## Installation (ubuntu 22.04)

    sudo su
    apt install python3 python3-pip
    cd /opt
    git clone git@github.com:jTheCreator21/ada2025-software-installer.git
    cd ada2025-software-installer
    python3 -m venv env
    source env/bin/activate
    pip3 install -r requirements.txt
    exit

## Optional configuration
You can also set the following optional environment variables to further configure Ada2025 Software Installer:

```bash
HOST # defaults to 127.0.0.1
PORT # defaults to 7322
DEBUG # set to "True" in order to enable debug mode
DL_PATH # defaults to /home/ubuntu/Downloads/
```

## JSON file
A JSON file has been created in the file server named "software.json", it is located in the "/var/www/html/ada-software-files/containers" directory. This holds the hiearchy of files that contain the software names, descriptions of the software, all available versions of the software and associated files that are needed for the installation of the software. This information is also stored in the Ada database for Software, this data is loaded from the database for use in the Ada Software Installer.