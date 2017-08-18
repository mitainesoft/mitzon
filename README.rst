###################################################################################
# Mitainesoft Garage (c) 2017                                                     #
# HW: garage raspberry-pi arduino                                                 #
# Code: Python3 with cherrypy, nanpi                                              #
# Purpose: Supervise garage door opening. Generate Alarms if required.            #
#          Allow remote open.                                                     #
#          Security via certificates and other fireall options                    #
# SCRUM board: https://github.com/mitainesoft/garage/projects                     #
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
        
    ** Linux **
    # In linux Debian or in Oracle VirtualBox,

    # Install raspbian Jessy v8.

        root@nomiberry:/etc# cat os-release
            PRETTY_NAME="Raspbian GNU/Linux 8 (jessie)"
            NAME="Raspbian GNU/Linux"
            VERSION_ID="8"
            VERSION="8 (jessie)"
            ID=raspbian
            ID_LIKE=debian
            HOME_URL="http://www.raspbian.org/"
            SUPPORT_URL="http://www.raspbian.org/RaspbianForums"
            BUG_REPORT_URL="http://www.raspbian.org/RaspbianBugs"


    ** Passwords **

    Immediatly change raspberry default passwords and assign one to root (optional security breach to avoid sudo !)

    passwd pi

    sudo passwd root

    #Note iptables should specify which device can login in later steps.


    ** install cherrypy for python3 **
      
        pip3 install cherrypy --upgrade
        pip3 install cheroot

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


    ** Add mitainesoft to sudoers **

    cd /etc/sudoers.d
    cp 010_pi-nopasswd 010_mitainesoft-nopasswd

    #remove pi from sudoers?!?

    #Change line
        pi ALL=(ALL) NOPASSWD: ALL
    to
        mitainesoft ALL=(ALL) NOPASSWD: ALL

    ** Setup package dir **


    su root
    mkdir -p /opt/mitainesoft/
    chown -R mitainesoft:mitainesoft /opt/mitainesoft

    cd /opt/mitainesoft/
    
2.  Install or Upgrade garage packages
    #Upload package to /opt/mitainesoft as user mitainesoft
    
    su - mitainesoft
    cd /opt/mitainesoft/
    tar -zxvf  garage-1.1.1.tar.gz

    mkdir -p /opt/mitainesoft/garage-1.1.1/log
    chmod 700 /opt/mitainesoft/garage-1.1.1/*.bash

    #if untar with other user
    # su - root
    #chown -R mitainesoft:mitainesoft /opt/mitainesoft


    ** Edit config **
    su - mitainesoft
    cd /opt/mitainesoft/garage-1.1.1/config
    cp garage_backend.template garage_backend.config
    # cp ../../garage/config/garage_backend.config .
    cd /opt/mitainesoft/garage-1.1.1

    #3 steps below may not be required
    su - root
    cd /opt/mitainesoft
    chown -R mitainesoft:mitainesoft /opt/mitainesoft
    exit

    #Customize config for notif email addresses and accoounts !

    ** Change apache2 index.html default link **

        su - root
        ls -l
        #IF not done already !
        cd /var/www
        rm html
        ln -s /opt/mitainesoft/garage/GarageFrontend html

     ** Fix garage start boot script
        cd /etc/init.d
        cp /opt/mitainesoft/garage/scripts/garage /etc/init.d
        chmod 755 /opt/mitainesoft/garage/scripts/garage
        cd /etc/rc3.d
        ln -s ../init.d/garage S99garage

        # Try it
        /etc/init.d/garage

    ** Edit mitainesoft crontab **
        su - mitainesoft
        crontab -e
        #delete nohup file
        0 5 * * 1 cp /dev/null /opt/mitainesoft/garage/GarageBackend/nohup.out > /dev/null 2>&1
        0,15,30,45 * * * * /opt/mitainesoft/garage/watchdog_mitaine_garage.bash  > /dev/null 2>&1


    ** Change active version of garage **
    su - mitainesoft
    cd /opt/mitainesoft/
    rm garage
    ln -s garage-1.1.1 garage

    ** Restart garage **
        #Check if running
        su - mitainesoft
        ps -eaf | grep /opt/mitainesoft/garage/GarageBackend/garageURLCmdProcessor.py | grep -v grep
        cd /opt/mitainesoft/garage
        ./garage.bash


3.  Test
Outputs in main Garage Backend console


 curl --cacert /opt/mitainesoft/security/mitainesoftsvr.pem  -X POST -d '' https://192.168.1.83:8050/GarageDoor/status/0



    a) Test Status
    curl -X POST -d '' https://192.168.1.83:8050/GarageDoor/status/0

    b) Test Open Close
    curl -X POST -d '' https://192.168.1.83:8050/GarageDoor/open/0
    curl -X POST -d '' https://192.168.1.83:8050/GarageDoor/close/0

    c) Test lock/Unlock
    curl -X POST -d '' https://192.168.1.83:8050/GarageDoor/lock/0
    curl -X POST -d '' https://192.168.1.83:8050/GarageDoor/close/0
    curl -X POST -d '' https://192.168.1.83:8050/GarageDoor/open/0



    f) Test Status
    curl -X POST -d '' http://192.168.1.83:8050/GarageDoor/status/0

    g) Test Open Close
    curl -X POST -d '' http://192.168.1.83:8050/GarageDoor/open/0
    curl -X POST -d '' http://192.168.1.83:8050/GarageDoor/close/0

    h) Test lock/Unlock
    curl -X POST -d '' http://192.168.1.83:8050/GarageDoor/lock/0
    curl -X POST -d '' http://192.168.1.83:8050/GarageDoor/close/0
    curl -X POST -d '' http://192.168.1.83:8050/GarageDoor/open/0

    curl -X POST -d '' http://192.168.1.83:8050/GarageDoor/lock/0
    curl -X POST -d '' http://192.168.1.83:8050/GarageDoor/close/0
    curl -X POST -d '' http://192.168.1.83:8050/GarageDoor/open/0


 d)Test Relay
curl -X POST -d '' http://192.168.1.83:8050/GarageDoor/testRelay/2



4.  Enable Security on Raspberry PI Raspbian


 ** Setting up a Mitainesoft Garage (MG) Embedded Certificate Authority **

    This appendix describes the procedure for implementing an embedded
    Certificate Authority (CA) in the mitainesoft garage solution (MGS),
    then utilize this CA to generate a server key pair and certificate
    signing request (CSR), and finally have the Rasp+ embedded CA sign the
    CSR. The signing of the CSR allows the server or component certificate
    to be used in the MGS solution by the various MGS components
    communicating on the OAM network using secure protocols such as
    REST over HTTPS, HTTPS and FTPS.

    Perform a clean install of Debian (or install the latest Raspbian PIXEL
    image on the Raspberry Pi) and boot up the host. It’s ok to have network access for now.
    For my Raspberry Pi I followed Raspbian Setup (Raspberry Pi) (you don’t need to install
    any of those packages in that link, just upgrade).
    If you’re using Debian be sure to create an encrypted LVM or partition.
    On a Raspberry Pi you can follow my guide to encrypt the main partition:
    aspberry Pi LUKS Root Encryption
    Upgrade all of your packages since this will be the last time the system will
    have internet access: sudo apt-get update && sudo apt-get upgrade.
    sudo reboot in case a new kernel was installed.

    Finally install these required packages: sudo apt-get install qrencode acl
    Boot Date Prompt on Raspberry Pi
    Raspberry Pis don’t have real time clocks so they don’t keep track of the time
    when powered off. Usually they handle this by getting the current time from the
    internet after booting up. However since our root CA will never have internet
    access again we need to always set the current time every time it boots up.


** Time NTP Raspberry **
    Since time is very important for signing certificates we’ll want to avoid
    forgetting this. You can install this systemd file to have it prompt you for the
    current time before the Raspberry Pi finishes booting up, guaranteeing you won’t forget:

    # Prompt for current date during boot.
    #
    # https://github.com/Robpol86/robpol86.com/blob/master/docs/_static/date-prompt.service
    #
    # Stops the system from booting up to 2 minutes or until user enters the
    # current time in the console. Useful for Raspberry Pis and other systems
    # with no real time clocks.
    #
    # Save as: /etc/systemd/system/date-prompt.service
    # Enable with: systemctl enable date-prompt.service

    [Unit]
    After=fake-hwclock.service
    After=systemd-fsck-root.service systemd-fsck@dev-mmcblk0p1.service
    Before=sysinit.target plymouth-start.service
    DefaultDependencies=no
    Description=Prompt for current date during boot

    [Service]
    Environment="P=Enter the current date (e.g. Feb 11 5:17 PM): "
    ExecStartPre=-/bin/plymouth deactivate
    ExecStart=/bin/bash -c 'until read -ep "$P" R; [ ! -z "$R" ] && date -s "$R"; do :; done'
    ExecStartPost=-/bin/plymouth reactivate
    ExecStopPost=-/bin/plymouth reactivate
    RemainAfterExit=yes
    StandardError=inherit
    StandardInput=tty
    StandardOutput=inherit
    TimeoutSec=120
    Type=oneshot

    [Install]
    WantedBy=sysinit.target



** Backup ssl file **
    su - root
    cd /etc/ssl
    mv openssl.cnf openssl.orig
    cp openssl.cnf openssl.cnf.mgsCA
    cp openssl.cnf openssl.cnf.4ServerCerts
    chmod 644 openssl*


** Fix CA.pl script for Method#2 **
    su - root
    cd /usr/lib/ssl/misc
    cp CA.pl CA_mitainesoft.pl
    cp CA.pl CA.pl.orig

    vi CA_mitainesoft.pl

	Locate -sign|-signreq and add –extensions v3_req after policy_anything in CA_mitainesoft.pl

        Before:
        $CA -policy policy_anything -out newcert.pem -infiles newreq.pem
        After:
        $CA -policy policy_anything -extensions v3_req -out newcert.pem -infiles newreq.pem


    :wq

** Prepare SSL Files **

    #sftp openssl.cnf.mgsCA & openssl.cnf.4ServerCerts from this package to /etc/ssl

    root@nomiberry:/etc/ssl# diff  openssl.orig  openssl.cnf.4ServerCerts
        < dir           = ./demoCA              # Where everything is kept
        ---
        > dir           = /root/ca              # Where everything is kept
        50c50
        < certificate   = $dir/cacert.pem       # The CA certificate
        ---
        > certificate   = $certs/ca.cert.pem    # The CA certificate
        55c55
        < private_key   = $dir/private/cakey.pem# The private key
        ---
        > private_key   = $dir/private/ca.key.pem       # The private key
        73c73
        < default_days  = 365                   # how long to certify for
        ---
        > default_days  = 3650                  # how long to certify for
        75c75
        < default_md    = default               # use public key default MD
        ---
        > default_md    = sha256                # use public key default MD
        107a108
        > default_md            = sha256
        109c110
        < attributes            = req_attributes
        ---
        > #attributes           = req_attributes
        125c126
        < # req_extensions = v3_req # The extensions to add to a certificate request
        ---
        > req_extensions = v3_req # The extensions to add to a certificate request
        129c130
        < countryName_default           = AU
        ---
        > countryName_default           = CA
        134c135
        < stateOrProvinceName_default   = Some-State
        ---
        > stateOrProvinceName_default   = QUEBEC
        136a138,139
        > localityName_default            = ILE-BIZARD
        >
        139c142,143
        < 0.organizationName_default    = Internet Widgits Pty Ltd
        ---
        > 0.organizationName_default      = mitainesoft.net
        >
        146c150
        < #organizationalUnitName_default       =
        ---
        > organizationalUnitName_default        = Mitaine
        150a155
        >
        152a158,159
        > emailAddress_default            = mitainesoft@gmail.com
        >
        191c198
        < nsComment                     = "OpenSSL Generated Certificate"
        ---
        > #nsComment                    = "OpenSSL Generated Certificate"
        222a230,231
        > extendedKeyUsage = serverAuth, clientAuth
        > subjectAltName = @alt_names
        350a360,363
        >
        >
        > [ alt_names ]
        > DNS.1 = *.mitainesoft.net



    root@nomiberry:/etc/ssl# diff  openssl.orig  openssl.cnf.mgsCA
        < dir           = ./demoCA              # Where everything is kept
        ---
        > dir           = /root/ca              # Where everything is kept
        50c50
        < certificate   = $dir/cacert.pem       # The CA certificate
        ---
        > certificate   = $certs/ca.cert.pem    # The CA certificate
        55c55
        < private_key   = $dir/private/cakey.pem# The private key
        ---
        > private_key   = $dir/private/ca.key.pem# The private key
        73c73
        < default_days  = 365                   # how long to certify for
        ---
        > default_days  = 3650                  # how long to certify for
        75c75
        < default_md    = default               # use public key default MD
        ---
        > default_md    = sha256                # use public key default MD
        107a108
        > default_md            = sha256
        109c110
        < attributes            = req_attributes
        ---
        > #attributes           = req_attributes
        125c126,127
        < # req_extensions = v3_req # The extensions to add to a certificate request
        ---
        > req_extensions = v3_req
        > # The extensions to add to a certificate request
        129c131
        < countryName_default           = AU
        ---
        > countryName_default           = CA
        134c136
        < stateOrProvinceName_default   = Some-State
        ---
        > stateOrProvinceName_default   = QUEBEC
        136a139
        > localityName_default            = ILE-BIZARD
        139c142
        < 0.organizationName_default    = Internet Widgits Pty Ltd
        ---
        > 0.organizationName_default      = mitainesoft.net
        146c149
        < #organizationalUnitName_default       =
        ---
        > organizationalUnitName_default        = Mitaine
        149a153
        > commonName_default              = MitainesoftCA
        152a157
        > emailAddress_default            = mitainesoft@gmail.com
        240c245
        < basicConstraints = CA:true
        ---
        > basicConstraints = CA:true, pathlen:0
        245a251
        > keyUsage = cRLSign, keyCertSign







** OpenSSL Directory Structure **

    Everything will live in /root/ca. It will also all be owned by root.
    Remember this computer is a dedicated CA

*** setup directories and permissions ***

     mkdir -p /root/ca/{certs,crl,csr,newcerts,private}
     setfacl -d -m u::rx -m g::rx -m o::rx /root/ca/private
     setfacl -d -m u::rx -m g::rx -m o::rx /root/ca/certs
     chmod 700 /root/ca/private
     touch /root/ca/index.txt
     tee /root/ca/serial <<< 1000

    Those setfacl commands set filesystem ACLs which enforce default
    maximum file permissions for new files/directories. A brief description for these directories:

        Directory	Description
        /root/ca/certs	Certificates are dumped here.
        /root/ca/crl	Certificate revocation lists.
        /root/ca/csr	Certificate signing request.
        /root/ca/newcerts	Not used in this guide.
        /root/ca/private	Private keys. VERY SENSITIVE.


    This is where we actually generate the root key and certificate.
    The root key is used to sign additional certificate pairs for specific
    devices/servers, and the root certificate is what you’ll export to
    clients that should trust any of these additional certificates.

    *** Warning ***

    The root key ca.key.pem you’ll be generating is the most sensitive file on this
    dedicated computer. Keep it as secure as possible. When openssl genrsa asks you
    for a password enter a unique and very secure password. Make sure setfacl worked a
    nd the permissions are: -r-------- 1 root root 1.8K Aug 15 12:21 private/ca.key.pem
    Note






 ** Generate root certificate and private key for embedded Certificate Authority (CA) **

    This section provides the procedure to create the private embedded MGS Certificate
    Authority that is used to sign (issue) the MGS server certificates.
    These certificates are only utilized for internal MGS communication, and are
    not be propagated externally from MGS (i.e. the Internet); therefore, they do not
    require a commercial trust anchor.  Instead, this embedded MGS CA acts as a trust
    anchor (i.e. Trusted Certificate Authority) for MGS servers and clients
    requiring certificates.




     rm  ./index.txt ; rm ./cacert.pem ; rm private/*  rm certs/*

     #Note: Common Name = mitainesoftCA

     #Use openssl made for CA anchor
     cd /etc/ssl
     mv openssl.cnf openssl.cnf.orig2  #Just in case!
     ln -s openssl.cnf.mgsCA openssl.cnf

     cd /usr/lib/ssl/misc
     ./CA_mitainesoft.pl -newca

        [OUTPUT...]
        root@nomiberry:/usr/lib/ssl/misc# ./CA_mitainesoft.pl -newca
        CA certificate filename (or enter to create)

        Making CA certificate ...
        Generating a 4096 bit RSA private key
        ..................................................................................................................................................................++
        ..............++
        writing new private key to '/root/ca/private/cakey.pem'
        Enter PEM pass phrase:
        Verifying - Enter PEM pass phrase:
        -----
        You are about to be asked to enter information that will be incorporated
        into your certificate request.
        What you are about to enter is what is called a Distinguished Name or a DN.
        There are quite a few fields but you can leave some blank
        For some fields there will be a default value,
        If you enter '.', the field will be left blank.
        -----
        Country Name (2 letter code) [CA]:
        State or Province Name [QUEBEC]:
        Locality Name [ILE-BIZ]:
        Organization Name [mitainesoft.net]:
        Organizational Unit Name [mitaine]:
        Common Name []:mitainesoftCA
        Email Address [mitainesoft@gmail.com]:
        Using configuration from /usr/lib/ssl/openssl.cnf
        Enter pass phrase for /root/ca/private/cakey.pem:
        Check that the request matches the signature
        Signature ok
        Certificate Details:
                Serial Number: 4096 (0x1000)
                Validity
                    Not Before: Jul 31 12:47:27 2017 GMT
                    Not After : Jul 30 12:47:27 2020 GMT
                Subject:
                    countryName               = CA
                    stateOrProvinceName       = QUEBEC
                    localityName              = ILE-BIZ
                    organizationName          = mitainesoft.net
                    organizationalUnitName    = mitaine
                    commonName                = mitainesoftCA
                    emailAddress              = mitainesoft@gmail.com
                X509v3 extensions:
                    X509v3 Subject Alternative Name:
                        DNS:nomiberry.mitainesoft.net
                    X509v3 Subject Key Identifier:
                        EB:80:8D:B9:70:7E:4F:2C:4:83:1A
                    X509v3 Authority Key Identifier:
                        keyid:EB:80:8D:B9:70:7E7:09:03:83:1A

                    X509v3 Basic Constraints: critical
                        CA:TRUE, pathlen:0
                    X509v3 Key Usage: critical
                        Digital Signature, Certificate Sign, CRL Sign
        Certificate is to be certified until Jul 30 12:47:27 2020 GMT (1095 days)

        Write out database with 1 new entries
        Data Base Updated

** Verify CA CERT **
    cd /root/ca
    openssl x509 -noout -text -in /root/ca/certs/ca.cert.pem

        Certificate:
        Data:
            Version: 3 (0x2)
            Serial Number: 4096 (0x1000)
        Signature Algorithm: sha256WithRSAEncryption
            Issuer: C=CA, ST=QUEBEC, L=ILE-BIZ, O=mitainesoft.net, OU=mitaine, CN=nomiberry/emailAddress=mitainesoft@gmail.com
            Validity
                Not Before: Jul 31 12:47:27 2017 GMT
                Not After : Jul 30 12:47:27 2020 GMT
            Subject: C=CA, ST=QUEBEC, L=ILE-BIZ, O=mitainesoft.net, OU=mitaine, CN=nomiberry/emailAddress=mitainesoft@gmail.com
            Subject Public Key Info:
                Public Key Algorithm: rsaEncryption
                    Public-Key: (4096 bit)
                    Modulus:
                        00:d9:8e:3d:3f:45:4a:49:6a:cf:08:c9:0f:aa:e7:
                        ...
                        ...
                        79:c4:2b:ba:9b:0b:23:12:bf:d3:2a:3c:05:c0:11:
                        41:b1:11
                    Exponent: 65537 (0x10001)
            X509v3 extensions:
                X509v3 Subject Alternative Name:
                    DNS:nomiberry.mitainesoft.net
                X509v3 Subject Key Identifier:
                    EB:80:8D:B9:70:7E:4F:2C:41:24:63:63:32:75:56:D7:09:03:83:1A
                X509v3 Authority Key Identifier:
                    keyid:EB:80:8D:B9:70:7E:4F:2C:41:24:63:63:32:75:56:D7:09:03:83:1A

                X509v3 Basic Constraints: critical
                    CA:TRUE, pathlen:0
                X509v3 Key Usage: critical
                    Digital Signature, Certificate Sign, CRL Sign
        Signature Algorithm: sha256WithRSAEncryption
             d5:bc:de:3e:45:fb:9b:94:bc:dc:99:34:94:f5:21:19:bb:c6:
             ...
             ...
             b7:67:ca:b7:fd:fc:0d:88:7b:22:d6:87:c4:4f:32:92:35:31:



** Generate the mitainesoft server/component key pair and CSR **

    This is stored under /usr/lib/ssl/misc and generates files with
    generic name such as newkey.pem  and newreq.pem

    Common Name should be diffferent!  use *.mitainesoft.net

     cd /etc/ssl
     rm openssl.cnf #Delete symbollic link created prior
     ln -s  openssl.cnf.4ServerCerts openssl.cnf

     cd /usr/lib/ssl/misc

     ./CA_mitainesoft.pl -newreq
        Generating a 4096 bit RSA private key
        ....................................................................++
        .....................................................................++
        writing new private key to 'newkey.pem'
        Enter PEM pass phrase:
        Verifying - Enter PEM pass phrase:
        -----
        You are about to be asked to enter information that will be incorporated
        into your certificate request.
        What you are about to enter is what is called a Distinguished Name or a DN.
        There are quite a few fields but you can leave some blank
        For some fields there will be a default value,
        If you enter '.', the field will be left blank.
        -----
        Country Name (2 letter code) [CA]:
        State or Province Name [QUEBEC]:
        Locality Name [ILE-BIZ]:
        Organization Name [mitainesoft.net]:
        Organizational Unit Name [mitaine]:
        Common Name []: [ USE A DIFFRENT NAME from -newca step!!! ]
        Email Address [mitainesoft@gmail.com]:
        Request is in newreq.pem, private key is in newkey.pem


        *** Verify 2 files ***
        cd /usr/lib/ssl/misc
        ls -l
            -rw-r----- 1 root root 1834 Jan  3 15:04 newkey.pem
            -rw-r----- 1 root root 1228 Jan  3 15:04 newreq.pem


 ** mitainesoft embedded CA signing the CSR Method#2**

    At this stage, the server/component private key is generated (newkey.pem)
    and the associated certificate signing request (newreq.pem). The next
    step is for the MGS embedded CA to sign the certificate signing request,
    and it is accomplished through the below procedure.


    su - root
    cd /usr/lib/ssl/misc

    ./CA_mitainesoft.pl -sign
        Using configuration from /usr/lib/ssl/openssl.cnf
        Enter pass phrase for /root/ca/private/cakey.pem:
        Check that the request matches the signature
        Signature ok
        Certificate Details:
                Serial Number: 4097 (0x1001)
                Validity
                    Not Before: Jul 31 13:28:51 2017 GMT
                    Not After : Aug 10 13:28:51 2018 GMT
                Subject:
                    countryName               = CA
                    stateOrProvinceName       = QUEBEC
                    localityName              = ILE-BIZ
                    organizationName          = mitainesoft.net
                    organizationalUnitName    = mitaine
                    commonName                = *.mitainesoft.net
                    emailAddress              = mitainesoft@gmail.com
                X509v3 extensions:
                    X509v3 Basic Constraints:
                        CA:FALSE
                    X509v3 Subject Key Identifier:
                        69:7C:23:81:5A:4A:C5:40:23:76:A7:DF:21:33:5A:16:DF:87:EF:7F
        Certificate is to be certified until Aug 10 13:28:51 2018 GMT (375 days)
        Sign the certificate? [y/n]:y


        1 out of 1 certificate requests certified, commit? [y/n]y
        Write out database with 1 new entries
        Data Base Updated
        Signed certificate is in newcert.pem



*** ERROR! Failed to update database TXT_DB error number 2 ? ***

        Problem:
        Because you have generated your own self signed certificate with the same CN (Common Name) information that the CA certificate that you’ve generated before.

        Enter another Common Name.


** Verify the server/component private key and associated certificate signing request (CSR) **
    At this point, the /usr/lib/ssl/misc directory should contain three files:

    - newkey.pem: the server/component private key
    - newreq.pem: the certificate signing request (CSR)
    - newcert.pem: the server/component signed certificate

    cd /usr/lib/ssl/misc
    ls -la *.pem
        -rw-r--r-- 1 root root 7157 Jul 31 09:28 newcert.pem
        -rw-r--r-- 1 root root 3394 Jul 31 09:27 newkey.pem
        -rw-r--r-- 1 root root 1858 Jul 31 09:27 newreq.pem


    The following command verifies that the certificate newcert.pem has been
    signed by a Trusted Certificate Authority.  In this case, the Trusted CA
    is the mitainesoft embedded CA, and the –verify option uses the MGS embedded
    CA certificate (cacert.pem) located in the /root/ca directory.

    openssl verify -CAfile /root/ca/certs/ca.cert.pem newcert.pem

        newcert.pem: OK


    ./CA_mitainesoft.pl  -verify /root/ca/certs/ca.cert.pem newcert.pem
        /root/ca/cacert.pem: OK
        newcert.pem: OK



** Rename the generated Files **

    The MGS solution uses a specific naming convention for the certificate and private key files, to rename the file appropriately, refer to the following example.
    For example:

    The file newkey.pem would become mitainesoftsvr.key.pem
    The file newcert.pem would become mitainesoftsvr.cert.pem


    Note:	All certificates generated by the MGS embedded CA are backed up in
    /root/ca/newcerts/.  The file name is represented by the certificate
    serial number which can be viewed in the index.txt located in the
    /root/ca directory.


    root@nomiberry:~/ca# cat index.txt
        V       270729194601Z           928E8DAB06690548        unknown /C=CA/ST=QUEBEC/O=mitainesoft.net/OU=Mitaine/CN=MitainesoftCA/emailAddress=mitainesoft@gmail.com
        V       270729200748Z           928E8DAB06690549        unknown /C=CA/ST=QUEBEC/L=ILE-BIZ/O=mitainesoft.net/OU=Mitaine/CN=192.168.1.83/emailAddress=mitainesoft@gmail.com



     #928E8DAB06690548 & 928E8DAB06690549 in this case


    Rename generated files:

    mv newcert.pem mitainesoftsvr.cert.pem
    mv newkey.pem mitainesoftsvr.key.pem


** Remove Paraphrase from Key **
    When restarting apache, apache asks for a pass-phrase each time you execute a restart.
    To avoid these requests, execute the following step.

    cd /usr/lib/ssl/misc
    ########cp  ca.key.pem  ca.key.pem.with_p

    cp mitainesoftsvr.key.pem mitainesoftsvr.key.pem.orig
    mv mitainesoftsvr.key.pem mitainesoftsvr.key.pem.with_p

    openssl rsa -in  mitainesoftsvr.key.pem.with_p -out  mitainesoftsvr.key.pem
                Enter pass phrase for mitainesoftsvr.key.pem.with_p: <MY PARAPHRASE>
                writing RSA key

    Expected Result:
      ca.key.pem now contains a pass-phrase.
     Verify as follows:
    # openssl rsa -in  ca.key.pem.with_p -noout -text  (will require pass-phrase)
    # openssl rsa -in  ca.key.pem -noout -text   (will NOT require pass-phrase)


** Distribution of Certificates and Private Keys to mitainesoft run directory **
    cd /usr/lib/ssl/misc
    cp  mitainesoftsvr.key.pem /opt/mitainesoft/security
    cp  mitainesoftsvr.cert.pem /opt/mitainesoft/security
    cat mitainesoftsvr.cert.pem mitainesoftsvr.key.pem > mitainesoftsvr.pem
    cp mitainesoftsvr.pem /opt/mitainesoft/security

    cd  /opt/mitainesoft/security/
    #Make certificates readeable by others
    chmod 444 *.pem

 ** ?!?!??  Combine the private key and the certificate **
    cd /root/ca
    #cat ./certs/ca.cert.pem  ./private/ca.key.pem > ./certs/garagemobile.pem


** Error curl: (60) SSL certificate problem: unable to get local issuer certificate **

    https://stackoverflow.com/questions/24611640/curl-60-ssl-certificate-unable-to-get-local-issuer-certificate

            We ran into this error recently. Turns out it was related to the root cert not being installed
            in the CA store directory properly. I was using a curl command where I was specifying the CA dir directly.
            curl --cacert /etc/test/server.pem --capath /etc/test ... This command was failing every time with
            curl: (60) SSL certificate problem: unable to get local issuer certificate.

            After using strace curl ..., it was determined that curl was looking for the root
            cert file with a name of 60ff2731.0, which is based on an openssl hash naming convetion. So I found
            this command to effectively import the root cert properly:

            ln -s rootcert.pem `openssl x509 -hash -noout -in rootcert.pem`.0
            which creates a softlink

            60ff2731.0 -> rootcert.pem
            curl, under the covers read the server.pem cert, determined the name of the root cert file (rootcert.pem), converted it to its hash name, then did an OS file lookup, but could not find it.

            So, the takeaway is, use strace when running curl when the curl error is obscure (was a tremendous help), and then be sure to properly install the root cert using the openssl naming convention.


     /etc/ssl/certs/71486fe4.0", 0x7eb2ac28) = -1 ENOENT (No such file or directory)

    cd ~/ca/certs

  cat ca.cert.pem /etc/ssl/certs/ca-certificates.crt >caBundle.cert.pem
  openssl x509 -hash -noout -in  caBundle.cert.pem


  openssl x509 -hash -noout -in caBundle.cert.pem

        71486fe4

    cd /usr/lib/ssl/certs
    ln -s  /root/ca/certs/caBundle.cert.pem 71486fe4.0





** test **
    #/root/ca/ is root only
    sudo curl --cacert /root/ca/certs/ca.CA.pem  -X POST -d '' https://192.168.1.83:8050/GarageDoor/status/0


    *** Test for Verify return code: 0 (ok) ***
    openssl s_client -connect 192.168.1.83:443
        CONNECTED(00000003)
        depth=1 C = CA, ST = QUEBEC, O = mitainesoft.net, OU = Mitaine, CN = MitainesoftCA, emailAddress = mitainesoft@gmail.com
        verify return:1
        depth=0 C = CA, ST = QUEBEC, L = ILE-BIZ, O = mitainesoft.net, OU = Mitaine, CN = 192.168.1.83, emailAddress = mitainesoft@gmail.com
        verify return:1
        ---
        Certificate chain
         0 s:/C=CA/ST=QUEBEC/L=ILE-BIZ/O=mitainesoft.net/OU=Mitaine/CN=192.168.1.83/emailAddress=mitainesoft@gmail.com
           i:/C=CA/ST=QUEBEC/O=mitainesoft.net/OU=Mitaine/CN=MitainesoftCA/emailAddress=mitainesoft@gmail.com
        ---
        Server certificate
        -----BEGIN CERTIFICATE-----
        MIIEADCCAuigAwIBAgIJAJKOjasGaQVJMA0GCSqGSIb3DQEBCwUAMIGIMQswCQYD
        ...
        ...
        8HjlRnurxh3rfAPUD/u/O5q6KGo=
        -----END CERTIFICATE-----
        subject=/C=CA/ST=QUEBEC/L=ILE-BIZ/O=mitainesoft.net/OU=Mitaine/CN=192.168.1.83/emailAddress=mitainesoft@gmail.com
        issuer=/C=CA/ST=QUEBEC/O=mitainesoft.net/OU=Mitaine/CN=MitainesoftCA/emailAddress=mitainesoft@gmail.com
        ---
        No client certificate CA names sent
        ---
        SSL handshake has read 1719 bytes and written 415 bytes
        ---
        New, TLSv1/SSLv3, Cipher is ECDHE-RSA-AES256-GCM-SHA384
        Server public key is 2048 bit
        Secure Renegotiation IS supported
        Compression: NONE
        Expansion: NONE
        SSL-Session:
            Protocol  : TLSv1.2
            Cipher    : ECDHE-RSA-AES256-GCM-SHA384
            Session-ID: 738D74319744690A526FDE060A8A8E87BC616E8C0635DF47415FCA93FE708D47
            Session-ID-ctx:
            Master-Key: 6942DFC5D88CDA54956A20C476134CDEF8FB1A353F9F89F817EA391083B807C9337460FE6A057016D81874D35F2C3AC6
            Key-Arg   : None
            PSK identity: None
            PSK identity hint: None
            SRP username: None
            TLS session ticket lifetime hint: 300 (seconds)
            TLS session ticket:
            0000 - e4 ec c9 0e c6 7a ab f5-39 5c 5b 72 7f f0 d8 80   .....z..9\[r....
            00b0 - 82 b8 ab 14 8b 04 dd e4-ff d8 69 94 86 36 c5 80   ..........i..6..

            Start Time: 1501539768
            Timeout   : 300 (sec)
            Verify return code: 0 (ok)



** Post activity After creating Embedded Certificates ?!? **

    The Original openssl.cnf must be restored after creating the embedded certificates.
    Otherwise, when regenerate the name server on the CUT server, it will fail with the
    following message:

    Auto configuration failed
    139830449022912:error:0200100D:system library:fopen:Permission denied:bss_file.c:169:fopen('/etc/pki/tls/openssl.cnf',
    'rb')

    Restore back original openssl

    cd /etc/ssl
    rm -f openssl.cnf
    cp openssl.orig openssl.cnf




** Install security certificates in Apache2

    cd /etc/apache2/sites-available
    vi 000-default.conf

    root@nomiberry:/etc/apache2/sites-available# cat 000-default.conf
    <VirtualHost *:80>

            ServerName www.example.com
            ServerAdmin admin@example.com

            # Redirect Requests to SSL
            Redirect permanent / https://192.168.1.83

            ErrorLog ${APACHE_LOG_DIR}/example.com.error.log
            CustomLog ${APACHE_LOG_DIR}/example.com.access.log combined

    </VirtualHost>
    <VirtualHost *:443>
            # The ServerName directive sets the request scheme, hostname and port that
            # the server uses to identify itself. This is used when creating
            # redirection URLs. In the context of virtual hosts, the ServerName
            # specifies what hostname must appear in the request's Host: header to
            # match this virtual host. For the default virtual host (this file) this
            # value is not decisive as it is used as a last resort host regardless.
            # However, you must set it for any further virtual host explicitly.
            #ServerName www.example.com

            ServerAdmin webmaster@localhost
            DocumentRoot /var/www/html

            # Available loglevels: trace8, ..., trace1, debug, info, notice, warn,
            # error, crit, alert, emerg.
            # It is also possible to configure the loglevel for particular
            # modules, e.g.
            #LogLevel info ssl:warn
            LogLevel info ssl:info

            ErrorLog ${APACHE_LOG_DIR}/error.log
            CustomLog ${APACHE_LOG_DIR}/access.log combined

            # For most configuration files from conf-available/, which are
            # enabled or disabled at a global level, it is possible to
            # include a line for only one particular virtual host. For example the
            # following line enables the CGI configuration for this host only
            # after it has been globally disabled with "a2disconf".
            #Include conf-available/serve-cgi-bin.conf
            SSLEngine on
            SSLCertificateFile /opt/mitainesoft/security/mitainesoftsvr.cert.pem
            SSLCertificateKeyFile /opt/mitainesoft/security/mitainesoftsvr.key.pem
    </VirtualHost>



** Install certificates in cherrypy web server **

    Review section !
    pyOpenSSL not working

    #Install cython, takes 20mins without any indication that it is running. `ls -ltr /tmp` to monitor...
    pip3 install cython

    # already installed my pi
    pip3 install pyOpenSSL

    http://www.fcollyer.com/posts/cherrypy-only-http-and-https-app-serving/

    http://docs.cherrypy.org/en/latest/deploy.html?highlight=certificate

    Add the following lines in your CherryPy config to point to your certificate files:

        'cherrypy.server.ssl_certificate': "/opt/mitainesoft/security/mitainesoftsvr.cert.pem",
        'cherrypy.server.ssl_private_key': "/opt/mitainesoft/security/mitainesoftsvr.key.pem",


5.  PREVENT OTHER DEVICES TO ACCESS THE RASPBERRY, PERIOD !

    #Copy/Paste lines as required.
    vi /etc/iptables-garage.rule

        :INPUT ACCEPT [0:0]
        :FORWARD ACCEPT [0:0]
        :OUTPUT ACCEPT [818:146333]
        # Admin rule with ssh port 22
        -A INPUT -p tcp -m mac --mac-source XX:XX:XX:XX:XX:XX -m multiport --dports 22,8050,80,443 -j ACCEPT

        #User
        -A INPUT -p tcp -m mac --mac-source YY:YY:YY:YY:YY:YY -m multiport --dports 8050,80,443 -j ACCEPT

        #Raspberry itself
        #gmail
        -A OUTPUT -p tcp -m multiport --dports 465,587,993 -j ACCEPT
        -A INPUT  -p tcp -m multiport --sports 465,587,993 -j ACCEPT


        #DNS & NTP Raspberry
        -A OUTPUT -p udp -m multiport --dports 53,123 -m state --state NEW,ESTABLISHED -j ACCEPT
        -A INPUT  -p udp -m multiport --dports 53,123 -m state --state ESTABLISHED -j ACCEPT
        -A OUTPUT -p udp -m multiport --sports 53,123 -m state --state NEW,ESTABLISHED -j ACCEPT
        -A INPUT  -p udp -m multiport --sports 53,123 -m state --state ESTABLISHED -j ACCEPT

        #Drop everything else
        -A INPUT -p tcp -j DROP
        -A INPUT -p udp -j DROP
        COMMIT
      
    #Check and delete old rules list
    iptables --list
    iptables --flush
    
    #Put new list
    iptables-restore  </etc/iptables-garage.rule
    #Check new rules list
    iptables --list
    iptables --flush
    
    
    #Edit script to be loaded a boot time
    cd /etc/network/if-pre-up.d
    vi mitainesoft_iptables
        #!/bin/sh
        iptables-restore  </etc/iptables-garage.rule

    #Check if it works !
    init 6
    
    #relogin
    #
    iptables --list
        root@nomiberry:~# iptables --list
        Chain INPUT (policy ACCEPT)
        target     prot opt source               destination
        ACCEPT     tcp  --  anywhere             anywhere             MAC XX:XX:XX:XX:XX:XX multiport dports ssh,8050,http,https
        ACCEPT     tcp  --  anywhere             anywhere             MAC YY:YY:YY:YY:YY:YY multiport dports 8050,http,https
        ACCEPT     tcp  --  anywhere             anywhere             MAC ZZ:ZZ:ZZ:ZZ:ZZ:ZZ multiport dports 8050,http,https
        ACCEPT     tcp  --  anywhere             anywhere             MAC Z1:Z1:Z1:Z1:Z1:Z1 multiport dports 8050,http,https
        DROP       tcp  --  anywhere             anywhere
        DROP       udp  --  anywhere             anywhere

        Chain FORWARD (policy ACCEPT)
        target     prot opt source               destination

        Chain OUTPUT (policy ACCEPT)
        target     prot opt source               destination


6. Packaging
    ** Reference **
    - https://packaging.python.org/tutorials/distributing-packages
    - https://docs.python.org/3.4/distutils/builtdist.html

    ** pre-requisite **
    - Linux terminal (raspberry Jessie, forget Windows !)
    - git installed
    - Need checkin permissions to mitainesoft, or comment subprocess.call (vcscmd_array[i]) in setup.py
    - python3 installed 

    
    #open Linux terminal on garage raspberry pi 
    su - root
    iptables --list
    iptables --flush
    #Push code from development PC!
    su - [git user]
    cd /git/garage
    python3 setup.py sdist

    

    
  #Package is under dist



7. HW

a) Raspberry Temperature Overheat !

    #Check the raspberry temperature.  The MGS dashboard will turn off the screen
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


8.  Design Env 
    su - pi
    mkdir -p /home/pi/garage/log/
    
    
9. Stuff

    ** Remove ^M Windows transfer dos2unix raspbian **
    perl -i -pe 's/\r\n$/\n/g' MYFILENAME

    ** apache sym links **
        root@nomiberry:/var/www# ls -la
        total 12
        drwxr-xr-x  3 root root 4096 Jul 16 16:19 .
        drwxr-xr-x 12 root root 4096 Dec  1  2016 ..
        lrwxrwxrwx  1 root root   31 Jul 16 16:19 dev_html -> /home/pi/garage/GarageFrontend/
        lrwxrwxrwx  1 root root    8 Jun 28 17:24 html -> dev_html
        drwxr-xr-x  2 root root 4096 Jun  3 16:28 html.orig
        lrwxrwxrwx  1 root root   38 Jun 28 17:22 pkg_html -> /opt/mitainesoft/garage/GarageFrontend


 ** Notification **

    gmail:
    https://www.google.com/settings/security/lesssecureapps

            self.email_server = smtplib.SMTP_SSL(self.getConfigParam("EMAIL_ACCOUNT_INFORMATION","SMTP_SERVER"), 465)
            self.email_server.ehlo()
            log.info("Login with %s" % self.getConfigParam("EMAIL_ACCOUNT_INFORMATION","USER"))
            self.email_server.login(self.getConfigParam("EMAIL_ACCOUNT_INFORMATION","USER"), \
                                    self.getConfigParam("EMAIL_ACCOUNT_INFORMATION","PASSWORD"))


