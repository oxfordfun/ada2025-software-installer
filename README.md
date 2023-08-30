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
