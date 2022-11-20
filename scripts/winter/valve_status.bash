 #!/bin/bash
 
 while [ 1 == 1 ] ; do 
   clear; 
   date
   echo
   for x in 0 1 2 3 4 5 6 7 8 ; do 
      echo ---- $x -----; 
      curl -k -d ''  https://192.168.1.92:8050/Valve/status/$x; 
      echo; echo; 
   done; 
   sleep 29; 
done
