 #!/bin/bash

 # 20221015
 # Empty zone winter
 # Set compressor valve to 60psi
  for x in 7 8 6 5 4 3 2 1 0 7 8 6 5 4 3 2 1 0 7 8 6 5 4 3 2 1 0 7 8 6 5 4 3 2 1 0 7 8 6 5 4 3 2 1 0  ; do 
    echo ---- $x -----; 
    curl -k -d ''  https://192.168.1.92:8050/Valve/manualopen/$x; 
    echo open $x; 
    sleep 60; 
    echo close $x; 
    curl -k -d ''  https://192.168.1.92:8050/Valve/close/$x; 
    echo ----; 
    date; 
    sleep 120; 
    echo; 
    date; 
    echo; 
    echo; 
 done
 
 
 #  while [ 1 == 1 ] ; do clear; for x in 0 1 2 3 4 5 6 7 8 ; do echo ---- $x -----; curl -k -d ''  https://192.168.1.92:8050/Valve/status/$x; echo; echo; done; sleep 29; done
