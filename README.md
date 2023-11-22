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
```

## Retrieving the software
The software is stored on the file server, all of the software directories can be found in the "/var/www/html/ada-software-files/containers/" directory. The URL for each piece of software is stored in the Ada database in the "Software" table. This data is then read and outputted into a JSON format by Ada, which is then read by the Ada2025 Software Installer in order to display the information about the software as well as downloading the software.