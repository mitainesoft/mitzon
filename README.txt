###################################################################################
# Mitainesoft Garage (c) 2017                                                     #
# HW: garage raspberry-pi arduino                                                 #
# Code: Python3 with cherrypy, nanpi                                              #
# Purpose: Supervise garage door opening. Generate Alarms if required.            #
#          Allow remote openening.                                                #
#          Security via certificates and other fireall options TBD...             #
# SRUM board: https://github.com/mitainesoft/garage/projects                      #
###################################################################################

 __        __         _      _         ____                                      _ 
 \ \      / /__  _ __| | __ (_)_ __   |  _ \ _ __ ___   __ _ _ __ ___  ___ ___  | |
  \ \ /\ / / _ \| '__| |/ / | | '_ \  | |_) | '__/ _ \ / _` | '__/ _ \/ __/ __| | |
   \ V  V / (_) | |  |   <  | | | | | |  __/| | | (_) | (_| | | |  __/\__ \__ \ |_|
    \_/\_/ \___/|_|  |_|\_\ |_|_| |_| |_|   |_|  \___/ \__, |_|  \___||___/___/ (_)
                                                       |___/                       


1. INSTALLATION INSTUCTIONS

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
        Step 1 — Installing Git with APT
        Before you install Git, make sure that your package lists are updated by executing the following command:

        sudo apt-get update
        Install Git with apt-get in one command:

        sudo apt-get install git-core

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

2. Notofication
    
    gmail:
    https://www.google.com/settings/security/lesssecureapps
    
            self.email_server = smtplib.SMTP_SSL(self.getConfigParam("EMAIL_ACCOUNT_INFORMATION","SMTP_SERVER"), 465)
            self.email_server.ehlo()
            log.info("Login with %s" % self.getConfigParam("EMAIL_ACCOUNT_INFORMATION","USER"))
            self.email_server.login(self.getConfigParam("EMAIL_ACCOUNT_INFORMATION","USER"), \
                                    self.getConfigParam("EMAIL_ACCOUNT_INFORMATION","PASSWORD"))
            
3. Other references

        Clone
        1.cd /c/git 
        2. git clone ssh://gerrit.ericsson.se:29418/mdn/pids.git 


        View bracnhes
        •git gui 
        •git log --graph --decorate --oneline --all ?git show ??? 

        •git log --graph --decorate --oneline M026_changes 

        Checkout branch

        git branch -a 

        git checkout cp33 

        git checkout -b ec33 origin/ec33 


        Logs
          git log --decorate=full --pretty=format:'%C(yellow)%H%Creset %C(bold yellow)%d%Creset %C(red)%ad%Creset %s'
          git branch -a -v



        Commits
        reset the author:
            git commit --amend --reset-author




        Sandbox instructions
        git checkout master
        git co -b  sandbox/<userid>/<anyBranchName>
        .
        .    changes¡K
        .
        git   add    .
        git commit ¡Va ¡Vm  ¡§message¡¨ 
        git push    --set-upstream   origin     sandbox/<userid>/<anyBranchName>


    ** debian package **
    - python3-pip
    - git
    - ssh
    - 


    ** Device **
    chmod 777 /dev/ttyUSB0





