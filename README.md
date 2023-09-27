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
    chmod +x ./wrapper_script.sh # (OPTIONAL STEP)
    cp ada2025-software-installer.desktop /home/ubuntu/Desktop/ # or wherever your desktop is (OPTIONAL STEP)
    chown ubuntu /home/ubuntu/Desktop/ada2025-software-installer.desktop # or whatever your user is (OPTIONAL STEP)
    chmod +x /home/ubuntu/Desktop/ada2025-software-installer.desktop # (OPTIONAL STEP)
    exit

## Optional configuration
You can also set the following optional environment variables to further configure Ada2025 Software Installer:

```bash
HOST # defaults to 127.0.0.1
PORT # defaults to 7322
DEBUG # set to "True" in order to enable debug mode
FS_URL # defaults to https://ada-files.oxfordfun.com/software/containers/
DL_PATH # defaults to /home/ubuntu/Downloads/
```

## JSON file
A JSON file has been created in the server named "software.json", it is located in the "/var/www/html/ada-software-files/containers" directory. This holds the hiearchy of files that contain the software names, versions and associated files that are needed for the installation of the software. The JSON file is loaded into the python program and the names and versions are extraced from it to create two lists, one for the names of the software and one for the versions of each piece of software.

## Cron job
A cron job has been used to keep the JSON file in the server up to date. The command is run every hour on the 59th minute of each hour.
Here is the command:
```bash
59 * * * * tree -J > software.json
```