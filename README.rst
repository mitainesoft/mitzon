###################################################################################
# Mitainesoft Garage (c) 2017                                                     #
# HW: garage raspberry-pi arduino                                                 #
# Code: Python3 with cherrypy, nanpi                                              #
# Purpose: Supervise garage door opening. Generate Alarms if required.            #
#          Allow remote open.                                                     #
#          Security via certificates and other fireall options TBD...             #
# SRUM board: https://github.com/mitainesoft/garage/projects                      #
###################################################################################

 __        __         _      _         ____                                      _ 
 \ \      / /__  _ __| | __ (_)_ __   |  _ \ _ __ ___   __ _ _ __ ___  ___ ___  | |
  \ \ /\ / / _ \| '__| |/ / | | '_ \  | |_) | '__/ _ \ / _` | '__/ _ \/ __/ __| | |
   \ V  V / (_) | |  |   <  | | | | | |  __/| | | (_) | (_| | | |  __/\__ \__ \ |_|
    \_/\_/ \___/|_|  |_|\_\ |_|_| |_| |_|   |_|  \___/ \__, |_|  \___||___/___/ (_)
                                                       |___/                       

1. INSTALLATION INSTRUCTIONS

    ** Install Arduino Image **
    First of all, you need to build the firmware and upload it on your Arduino, 
    to do that clone the nanpy-firmware repository on Github or download it from PyPi.
    
    https://github.com/nanpy/nanpy

        git clone https://github.com/nanpy/nanpy-firmware.git
        cd nanpy-firmware
        ./configure.sh

        load and upload nanpy.ino
        

    In linux Debian in Oracle VirtualBox

    ** install cherrypy for python3 **

        Download & extract cherrypy tar gz i.e. CherryPy-8.1.2.tar.gz
        cd cherrypy
        $ python3 setup.py install

    ** install nanpy for raspberry pi arduino
        # https://pypi.python.org/pypi/nanpy
        pip3 install nanpy


    ** install git **
        Step 1 � Installing Git with APT
        Before you install Git, make sure that your package lists are updated by executing the following command:

        sudo apt-get update
        Install Git with apt-get in one command:

        sudo apt-get install git-core


    ** Create mitainesoft user **
        sudo adduser mitainesoft
        #Answers to questions and passwd not important
        # Keep in mind that this user will have access to the USB port!
        # You can change later with  'sudo passwd mitainesoft'

    ** Add mitainesoft to dialout group
        sudo vi /etc/group

            dialout:x:20:pi,mitainesoft

    ** Setup package dir **


    su root
    mkdir -p /opt/mitainesoft/
    chown -R mitainesoft:mitainesoft /opt/mitainesoft

    cd /opt/mitainesoft/
    #Upload packge to /opt/mitainesoft as user mitainesoft

    if Windows:
        sudo unzip garage-0.0.3.zip  <-- Bad CTRL-M
    if Linux:
        sudo tar -zxvf garage-0.0.3.tar.gz
    su - mitainesoft
    cd /opt/mitainesoft/
    rm garage
    ln -s garage-0.0.3 garage
    mkdir -p /opt/mitainesoft/garage/log
    chmod 700 /opt/mitainesoft/garage/*.bash
    chown -R mitainesoft:mitainesoft /opt/mitainesoft


    ** Edit config **
    su - mitainesoft
    cd /opt/mitainesoft/garage
    cd /opt/mitainesoft/garage/config
    cp garage_backend.template garage_backend.config
    cd /opt/mitainesoft/garage

    cd /opt/mitainesoft
    su root
    chown -R mitainesoft:mitainesoft /opt/mitainesoft

    #Customize config for notif email addresses and accoounts !

    ** Change apache2 index.html default link **

        su - root
        ls -l
        #IF not done already !
        cd /var/www
        rm html
        ln -s /opt/mitainesoft/garage/GarageFrontend html

    ** Edit mitainesoft crontab **
        su - mitainesoft
        crontab -e
        #delete nohup file
        0 5 * * 1 cp /dev/null /opt/mitainesoft/garage/GarageBackend/nohup.out > /dev/null 2>&1
        0,15,30,45 * * * * /opt/mitainesoft/garage/watchdog_mitaine_garage.bash  > /dev/null 2>&1


    ** Restart garage **
        #Check if running
        su - mitainesoft
        ps -eaf | grep /opt/mitainesoft/garage/GarageBackend/garageURLCmdProcessor.py
        cd /opt/mitainesoft/garage
        ./garage.bash


2.  Test
Outputs in main Garage Backend console

a) Test Status
$ curl -X POST -d '' http://192.168.1.83:8050/GarageDoor/status/0

b) Test Open Close
curl -X POST -d '' http://192.168.1.83:8050/GarageDoor/open/0
curl -X POST -d '' http://192.168.1.83:8050/GarageDoor/close/0

c) Test lock/Unlock
curl -X POST -d '' http://192.168.1.83:8050/GarageDoor/lock/0
curl -X POST -d '' http://192.168.1.83:8050/GarageDoor/close/0
curl -X POST -d '' http://192.168.1.83:8050/GarageDoor/open/0

curl -X POST -d '' http://192.168.1.83:8050/GarageDoor/lock/0
curl -X POST -d '' http://192.168.1.83:8050/GarageDoor/close/0
curl -X POST -d '' http://192.168.1.83:8050/GarageDoor/open/0


 d)Test Relay
curl -X POST -d '' http://192.168.1.83:8050/GarageDoor/testRelay/2

3. Packaging
    Ref: https://packaging.python.org/tutorials/distributing-packages
    cd /git/mitaine/garage
    python3 setup.py sdist

    https://docs.python.org/3.4/distutils/builtdist.html
    python setup.py bdist --format=ztar
    
  #Package is under dist



4. HW

a) Raspberry Overheat !

    #Check the raspberry temperature.  The mdn dashboard will turn off the screen
    #  if temperature exceed a certain value (check in scipts!)
    #  the graphical display is creating overheat.
    # Make sure you ordered the cooling fan kit for the raspberry or it wont survive !

    watch -n 60 /opt/vc/bin/vcgencmd measure_temp
    # temp below 50C is OK !


5. DESIGN ENV SETUP

    ** ssh key **
        1. on linux where git will installed.
        2. Execute ssh-keygen -t rsa and accept all the default (press enter). The SSH public key will be generated in .ssh/ directory under your home directory, typically C:\Users\<username>\.ssh\id_rsa.pub on Windows.
        3. Enter your SSH key in https://github.com/mitainesoft in settings.
        4. If using Git on Unix, copy keys from Windows to Unix ~/.ssh. Keys are C:\Users\<username>\.ssh\id_rsa.pub and C:\Users\<username>\.ssh\id_rsa.


    ** git config **
        git config --global user.name "<your_signum>" (e.g. lmcpare, exxxxxx)
        git config --global user.email "<your_email_address>" (as it appears in Outlook, e.g. firstname.lastname@ericsson.com)


        *** OPTIONAL? ***
        git config --global core.autocrlf input
        git config --global color.ui true
        git config --global gui.encoding utf-8
        git config --global push.default upstream
        git config --global core.excludesfile <your-HOME>/.gitignore

        In general, you should merge your branches with the main branch. To configure Git to automatically set up new branches to merge with the remote branch they are tracking, run
        git config --global branch.autosetupmerge always


        If you like, you can also create aliases for common commands like so:
        git config --global alias.co checkout
        git config --global alias.ci commit
        git config --global alias.st status
        git config --global alias.br branch
        git config --global alias.up "pull --rebase"
        git config --global alias.lol "log --graph --decorate --oneline"
        git config --global alias.unadd "reset HEAD --"

        git config --global core.editor "\path\to\editor"
            For example the following line will make notepad++ (installed to default location) your global editor of files in git:
            git config --global core.editor "C:\Program Files (x86)\Notepad++\notepad++.exe"






    ** debian package **
    - python3-pip
    - git
    - ssh
    -



6. Stuff

6a. Notification

    gmail:
    https://www.google.com/settings/security/lesssecureapps

            self.email_server = smtplib.SMTP_SSL(self.getConfigParam("EMAIL_ACCOUNT_INFORMATION","SMTP_SERVER"), 465)
            self.email_server.ehlo()
            log.info("Login with %s" % self.getConfigParam("EMAIL_ACCOUNT_INFORMATION","USER"))
            self.email_server.login(self.getConfigParam("EMAIL_ACCOUNT_INFORMATION","USER"), \
                                    self.getConfigParam("EMAIL_ACCOUNT_INFORMATION","PASSWORD"))


