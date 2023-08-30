# ada2025-software-installer
## Installation (ubuntu 22.04)

    sudo apt install python3 python3-pip
    git clone git@github.com:jTheCreator21/ada2025-software-installer.git
    cd ada2025-software-installer
    python3 -m venv env
    source env/bin/activate
    pip3 install -r requirements.txt
    cp ada2025-software-installer.desktop /home/ubuntu/Desktop/ # or wherever your desktop is (OPTIONAL STEP)
    chmod +x /home/ubuntu/Desktop/ada2025-software-installer.desktop

## Optional configuration
You can also set the following optional environment variables to further configure Ada2025 Software Installer:

```bash
HOST # defaults to 127.0.0.1
PORT # defaults to 7322
DEBUG # set to "True" in order to enable debug mode
FS_URL # defaults to https://ada-files.oxfordfun.com/software/containers/
DL_PATH # defaults to /home/ubuntu/Downloads/
```