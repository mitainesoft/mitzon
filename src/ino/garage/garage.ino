/*
  Garage Systeme

  x relays that are either ON or OFF for aperiod of time.
  
  Number of switches is configurable.

 Circuit:
 * Ethernet shield attached to pins 10, 11, 12, 13
 * Analog inputs attached to pins A0 through A5 (optional)
 */

//#include <SPI.h>
#include <Ethernet.h>
#include <dht.h>

// Enter a MAC address and IP address for your controller below.

byte ip_mac_last_dig = 81;
byte mac[] = {  0xDE, 0xAD, 0xBE, 0xEF, 0xFE, ip_mac_last_dig};
IPAddress ip(192, 168, 1, ip_mac_last_dig);
char rev[] = "v0.00";

#define DEBUGLEVEL 2
// NUM_SWITCH # of controlled relays. 4 MAX !
#define NUM_SWITCH 4
#define NBR_RELAY_INSTALLED 4


////////////////////////////////////////////////////////////////////////
//VARIABLES DECLARATION
////////////////////////////////////////////////////////////////////////

char iptxt[20]="";
byte outp = 0;
boolean printLastCommandOnce = false;

boolean reading = false;
unsigned long timeConnectedAt=0;
unsigned long _led_flash_time_interval=0;

unsigned long pcounter=0;
unsigned long _currentMillis[NUM_SWITCH];
unsigned long _previousMillis[NUM_SWITCH];
unsigned long _timeLeftMillis[NUM_SWITCH];
//unsigned long _timeLeftMin=0;
byte on_off[NUM_SWITCH];  //HIGH or LOW

#define NBR_DURATIONS_CHOICES 5
#define TIME_YOU_HAVE_TO_MAKE_A_CHOICE 15000
#define TIMELEFTDEFAULT 900999
unsigned long _duration_available[]= {0,TIMELEFTDEFAULT,7202000,28802000,43202000};
//Test Values
//#define TIMELEFTDEFAULT 30999
//unsigned long _duration_available[]= {0,TIMELEFTDEFAULT,60000,90000,120000};

int _duration_choices[NUM_SWITCH];


// _timer_status
//    0 = off
//    1 = on
//    2 = expired
#define TIMER_OFF 0
#define TIMER_ON 1
#define TIMER_EXPIRED 2
byte _timer_status[NUM_SWITCH];

//Zone 0 is relay #1. 0 is array position.
#define ZONE_FOR_DURATION_CHOICE_LED_STATUS 0
// PUSHBUTTON_PRESS_LEVEL_SENSITIVITY 250 good quality connection !  175 is cheapo button !
#define PUSHBUTTON_PRESS_LEVEL_SENSITIVITY 250

// relay #1 = 7 20160807
#define RELAY1_DIGPIN 7
#define RELAY2_DIGPIN 6
#define RELAY3_DIGPIN 5
#define RELAY4_DIGPIN 4

#define PUSH_BUTTON_ANALOG_IN 0
#define DHT21_PIN 8
#define LED_STATUS_ZONE1_DIGITAL_OUT 9

// Select the pinout address
const byte outputAddress[] = {RELAY1_DIGPIN,RELAY2_DIGPIN,RELAY3_DIGPIN,RELAY4_DIGPIN}; //Allocate x spaces and name the output pin address.

const char *relayZoneDesc[] = { "Chasse-Garage", "Lum Sous-Sol", "Mega-Spot1", "Mega-Spot2" };
//char *tableFontColor[8] = { "#8B4513","#228B22","#FF8C00","#FF1493","#8A2BE2","#8A2BE2","#8A2BE2","#8A2BE2" }; // http://www.w3schools.com/colors/colors_names.asp

// Ethershield UNO PINS pins 4, 10, 11, 12, and 13.  4 conflict !?! with relay board?
// https://www.arduino.cc/en/Main/ArduinoEthernetShield

//boolean outputStatus[NBR_RELAY_INSTALLED]; //Create a boolean array for the maximum ammount.
const boolean relayTestMode=false;


//Html page refresh
const int refreshPage = 15; //default is 10sec. 
//Beware that if you make it refresh too fast, the page could become inacessable.


//Invert / reverse the output of the leds
const boolean outputInverted[] = {false,false,false,false}; //true or false
const boolean displayOnOffInverted[] = {true,false,false,false};
//define DEFAULT_ON_OFF 1
const byte _default_On_Off[] = {LOW,LOW,LOW,LOW};
const char *_LOW_HIGH_TXT[2]= {"LOW","HIGH"};
 
// This is done in case the relay board triggers the relay on negative, rather then on positive supply

String HTTP_req;            // stores the HTTP request


// Initialize the Ethernet server library
// with the IP address and port you want to use
// (port 80 is default for HTTP):
EthernetServer server(80);

// Temperature Humidite
dht DHT21;
unsigned long lastTempHumReadTime=0;
double _DHT21_TEMP_HUM[2];


void setup() {
  // Open serial communications and wait for port to open:
  Serial.begin(115200);
  while (!Serial) {
    ; // wait for serial port to connect. Needed for native USB port only
  }

  int prechk = DHT21.read11(DHT21_PIN);
  //Lire le sensor pour etablir la comm serie qui est bizarre au demarrage
//  delay(500);
  
  // start the Ethernet connection and the server:
  Ethernet.begin(mac, ip);
  server.begin();
  Serial.print(F("Garage Web Server is at "));
  Serial.println(Ethernet.localIP());
  for (int i=0;i<=3;i++) {
    //Serial.println(ip[i]) ;
    char ipbuf[10]="";
    sprintf(ipbuf,"%d",ip[i]);
    strcat(iptxt,ipbuf);
    if (i<3) {
       strcat(iptxt,".");
    }
  }
  Serial.print(F("Version: "));
  Serial.println(rev);
  Serial.print(F("DHT LIBRARY VERSION: "));
  Serial.println(DHT_LIB_VERSION);

  initDigPin();
  Serial.print(F("Push Button Analog IN: "));
  Serial.println(PUSH_BUTTON_ANALOG_IN);
  Serial.print(F("DHT21 Temp/Hum Sensor Digital IN: "));
  Serial.println(DHT21_PIN);
  Serial.print(F("LED Zone1 Digital OUT: "));
  Serial.println(LED_STATUS_ZONE1_DIGITAL_OUT);
  Serial.println(F("Ethershield Digital pins: 4?, 10, 11, 12, 13"));

  initArrays();
  Serial.println();

  readTempDHT21(); 
}

/////////////////////////////////////////////////////////////////////////////////////////////
// loop !
/////////////////////////////////////////////////////////////////////////////////////////////

void loop() {

//  Serial.println("checkForClient: listen for incoming clients, and process requests...");
  checkForClient();

  processTimers();
  delay(500);
  if (millis() > (lastTempHumReadTime + 30000)){   
    readTempDHT21();
    lastTempHumReadTime=millis();
//    Serial.print("freeMemory()=");
//    Serial.println(freeMemory());
  }

  durationChoicesAnalogPins();
  checkButtonAnalog();


}


////////////////////////////////////////////////////////////////////////
//checkForClient Function
////////////////////////////////////////////////////////////////////////
//
void checkForClient(){

  EthernetClient client = server.available();
  boolean currentLineIsBlank = true;
  boolean sentHeader = false;
  String serlog="";
  String webCommand="";
  unsigned long lasttimemillis=0;
  unsigned long tmpmil=0;
  unsigned long tmpcurmil=0;
     
  if (client) {

    while (client.connected()) {
      
      if (client.available()) {
         //read user input
        char c = client.read();
        
        if (DEBUGLEVEL > 4) {
          if (reading == true || DEBUGLEVEL >=8) {
            serlog += String ("DEBUG c.read=");
            serlog += String(c); 
            serlog += String(" reading=");
            serlog += String(reading);
            Serial.println(serlog);
            serlog ="";
          }
        }
       
        
        if(c == '*'){
        }
        
        if(!sentHeader){
            printHtmlHeader(client); //call for html header and css
            printSwitchTable(client);
          //This is for the arduino to construct the page on the fly. 
          sentHeader = true;
        }

  
        //if there was reading but is blank there was no reading
        if(reading && c == ' '){
          reading = false;
          if (DEBUGLEVEL>5) {
            Serial.println();
            Serial.print(F("Command reading:'"));
            Serial.print(webCommand); 
            Serial.println(F("'"));
          }
          processCommand(webCommand);
          if (webCommand.indexOf("ajax_switch")) {
              reloadHTMLPage(client); 
          }
          webCommand="";
          //reloadHTMLPage(client);
          break;
        }
        
        // if there was user input switch the relevant output
        if(reading){
          webCommand+=String(c);
          currentLineIsBlank = false;
         
        }//end of switch switch the relevant output 
        //if there is a ? there was user input
        if(c == '?') {
          reading = true; //found the ?, begin reading the info
        }

        //if user input was blank
        if (c == '\n' && currentLineIsBlank){
          printLastCommandOnce = true;
          break;
        }
      }//if client avail
    }
    
  printHtmlFooter(client); //Prints the html footer
 
  } 
else
   {  //if there is no client 
      //And time of last page was served is more then a minute.
      if (millis() > (timeConnectedAt + 60000)){           
          timeConnectedAt=millis();
          if (DEBUGLEVEL>4) {
            Serial.println(F("No HTTP client for the last 60sec..."));           
          }
      }
   }


}

void reloadHTMLPage(EthernetClient client) {
  char buf[200];
//  client.println(F("<meta http-equiv=\"refresh\" content=\"0;url=192.168.2.177\"/>"));

  sprintf(buf,"<meta http-equiv=\"refresh\" content=\"0;url=%s\"/>",iptxt);
  client.println(buf);
        
}
////////////////////////////////////////////////////////////////////////
//processCommand Function
////////////////////////////////////////////////////////////////////////
int  processCommand(String webCmd) {
  int cmdid=-999;
  int setpin=LOW;
  String cmd="";
  String subcmd="";
  byte swi;

  cmd=webCmd.substring(0,4);
  subcmd=webCmd.substring(4);
  if (DEBUGLEVEL>3) {
    Serial.print(F("processCommand:'"));
    Serial.print(webCmd );
    Serial.print(F("'"));
    Serial.print(F(" (cmd:"));
    Serial.print(cmd);
    Serial.print(F(")  "));
    Serial.print(F(" (subcmd:"));
    Serial.print(subcmd);
    Serial.println(F(")"));
  }
  
  if (cmd == "cmd=") { 
    cmdid=subcmd.toInt();
    if (DEBUGLEVEL>3) {
      Serial.print(webCmd);
      Serial.print(F(" OK! ("));
      Serial.print(subcmd);
      Serial.print(F(")/("));
      Serial.print(cmdid);
      Serial.println(F(")") );
    }
    
    if ((cmdid % 2)==0) {
      cmdid -= 2;
      swi = cmdid/2;
      setpin = LOW;
      Serial.print(F("processCommand DISABLE relay:"));
    } else {
      cmdid -=3;
      swi = cmdid/2;
      Serial.print(F("processCommand ENABLE relay#"));
      setpin = HIGH; //Enable i.e. same as defualt value
    }  
    cmdid = cmdid/2;

    on_off[swi]=setpin;
    Serial.print(swi+1); 
    Serial.print(F(" set pin="));
    Serial.println(_LOW_HIGH_TXT[setpin]);
    triggerPin(swi,setpin);

    if (setpin==_default_On_Off[swi]) { 
      _timeLeftMillis[swi]=0;
      _timer_status[swi]=TIMER_OFF; //Timer Off
      _duration_choices[swi]=0; //reset
    } else {
        _timer_status[swi]=TIMER_ON; //Timer ON    
        _currentMillis[swi]=millis();
        _previousMillis[swi]=millis(); 
        //duration_choices[i]
        int tmp_next_choice=_duration_choices[swi]+1;
        if (tmp_next_choice>=NBR_DURATIONS_CHOICES) {
          // Next choice is 0
          _duration_choices[swi]=0;
        } else {
          // A few off choices
          _duration_choices[swi]=tmp_next_choice;
        }
        _timeLeftMillis[swi]=_duration_available[tmp_next_choice];
        _duration_choices[swi]=tmp_next_choice;
    }
  } else {
    Serial.print(cmd);
    Serial.print(F(" ?!? INVALID ?!? "));
    Serial.println(webCmd);
  }

  if (cmdid < 0) {
    Serial.print(F("\nInternal Server Error Invalid cmdid:"));
    Serial.print(cmdid);
    Serial.print(F("    Switch ID"));
    Serial.print(swi);
  }

  return (swi);
}


////////////////////////////////////////////////////////////////////////
//printLoginTitle Function
////////////////////////////////////////////////////////////////////////
//Prints html button title
void printLoginTitle(EthernetClient client){
      //    client.println(F("<div  class=\"group-wrapper\">");
          client.println(F("    <h2>Please enter the user data to login.</h2>"));
          client.println();
}

////////////////////////////////////////////////////////////////////////
//htmlHeader Function
////////////////////////////////////////////////////////////////////////
//Prints html header
 void printHtmlHeader(EthernetClient client){
          
          timeConnectedAt = millis(); //Record the time when last page was served.
          if (DEBUGLEVEL >6) {
            Serial.print(F("Serving html Headers at ms -"));
            Serial.println(timeConnectedAt); // Print time for debbugging purposes
          }
          //writeToEeprom = true; // page loaded so set to action the write to eeprom
          
          // send a standard http response header
          client.println(F("HTTP/1.1 200 OK"));
          client.println(F("Content-Type: text/html"));
          client.println(F("Connnection: close"));
          client.println();
          client.println(F("<!DOCTYPE html>"));
          client.println(F("<html>"));
          client.println(F("<head>"));

          // add page title 
          client.println(F("<title>Systeme Garage</title>"));
          client.println(F("<meta name=\"description\" content=\"System Garage2\"/>"));

          // add a meta refresh tag, so the browser pulls again every x seconds:
          client.print(F("<meta http-equiv=\"refresh\" content=\""));
          client.print(refreshPage);
          client.println(F("; url=/\">"));

          // add other browser configuration
          client.println(F("<meta name=\"apple-mobile-web-app-capable\" content=\"yes\">"));
          client.println(F("<meta name=\"apple-mobile-web-app-status-bar-style\" content=\"default\">"));
          client.println(F("<meta name=\"viewport\" content=\"width=device-width, user-scalable=no\">"));          

          //inserting the styles data, usually found in CSS files.
          client.println(F("<style type=\"text/css\">"));
          client.println(F(""));

           //and finally this is the end of the style data and header
          client.println(F("</style>"));          
          client.println(F("</head>"));

 } //end of htmlHeader

// Print Switch Table
int printSwitchTable(EthernetClient client)
{
  char txt[200];
  char stattxt[5]; //Big bg status in box
  char nextstattxt[5];  //Next status
  char revstattxt[5]; //Status reverse for button before when doing a cycle
  
  printpCounter();
  
  //now printing the page itself
  client.println(F("<body>"));
  client.println(F("<div class=\"view\">"));
  client.println(F("<div class=\"header-wrapper\">"));
  client.println(F("<h1><font size=\"30\" color=\"#191970\">Garage Systeme</font></h1>"));
  //http://www.w3schools.com/colors/colors_names.asp
  client.println(F("</div>"));

  client.print(F("<table border=1><tr>"));
    for(int swi=0; swi<NUM_SWITCH; swi++){
        client.print(F("<td>"));
        client.print(F("<form METHOD=get action=\""));
        client.print(F("\">"));
        sprintf(txt, "<h2><center>%s (#%d)</center></h2> ", relayZoneDesc[swi] ,swi+1); 
//        sprintf(txt, "<h2><center><font color=\"%s\"> %s (#%d) </font></center></h2> ", tableFontColor[swi], relayZoneDesc[swi] ,swi+1); 
        
        client.print(txt);
        
        //add_string(buf, txt, plen);
        if(on_off[swi] == _default_On_Off[swi]){
          client.print(F("<h1><center><font color=\"#00FF00\"> ")); //GREEN
          if (displayOnOffInverted[swi]) {
              client.print(F("ON"));
              strcpy(stattxt,"ON");
              strcpy(revstattxt,"OFF");
              strcpy(nextstattxt,"OFF"); //button text for next status
          } else {
              client.print(F("OFF"));
              strcpy(stattxt,"OFF");
              strcpy(revstattxt,"ON");
              strcpy(nextstattxt,"ON"); //button text for next status
          }
        } else { 
          char strbuf[20];
          getTimePrintOut(_timeLeftMillis[swi],strbuf);
          client.print(F("<h1><center><font color=\"#FF0000\"> ")); //RED
          if (displayOnOffInverted[swi]) {
            strcpy(stattxt,"OFF");
            strcpy(revstattxt,"ON");
            strcpy(nextstattxt,"OFF"); //button text for next status
          } else {
            strcpy(stattxt,"ON");
            strcpy(revstattxt,"OFF");
            strcpy(nextstattxt,"ON"); //button text for next status
          }
          sprintf(txt, "%s %s",stattxt, strbuf);
          client.print(txt);
        }
        client.print(F("  </font></center></h1><br> "));
        int tmpdur=_duration_choices[swi];
        int tmpnextdur=tmpdur+1;
        if (tmpnextdur>=NBR_DURATIONS_CHOICES) {
          tmpnextdur=0;
        }
        if(tmpnextdur>0) { //on_off[swi] == HIGH){
          sprintf(txt, "<input type=hidden name=cmd value=%03d>", 3 + swi * 2);
          client.print(txt); 
          char strbuf[20];
          getTimePrintOut(_duration_available[tmpnextdur],strbuf);
          sprintf(txt,"<input type=submit style=\"font-size:14pt;color:black;background-color:LightGray\" value=\"Switch %s %s \"></form>",nextstattxt,strbuf);
          //sprintf(txt,"<input type=submit value=\"Switch %s %s \"></form>",nextstattxt,strbuf);
          client.print(txt);
        } else {
          sprintf(txt, "<input type=hidden name=cmd value=%03d>", 2 + swi * 2); 
          client.print(txt); 

          //const char hbuf[]="style=\"font-size:14pt;color:black;background-color:white;border:3px solid #336600;padding:3px\"";
          const char hbuf[]=" style=\"font-size:14pt;color:black;background-color:white\" ";
          //Memory problems!!!

          sprintf(txt,"<input type=submit %s value=\"Switch %s \"></form>",hbuf, revstattxt);
          //sprintf(txt,"<input type=submit value=\"Switch %s \"></form>",revstattxt);
          client.print(txt);
        }
        //_duration_choices[swi]=tmpnextdur;
        client.print(F("</td>"));
      }
      client.print(F("</tr></table>"));
      
      sprintf(txt,"*** Meteocureuil   * Temperature:<font size=\"9\" color=\"blue\"> %dc </font>   \n * Humidite:<font size=\"9\" color=\"orange\"> %d%% </font>***",
          (int)_DHT21_TEMP_HUM[0],
          (int)_DHT21_TEMP_HUM[1]);
  client.println(F("\n<h2 align=\"left\"> "));
  client.println(txt);
  client.println(F("</h2>"));
  client.println(F("\n\n\n<h3 align=\"left\">*** Cadenas   * <font color=\"Maroon\">Lund:2341</font>   * <font color=\"DarkBlue\">Princecraft:4612</font> *** "));
  client.println(F("</h3>"));
  client.println(F("\n\n\n\n<h4 align=\"left\">&copy; MitaineSoft 2016 - "));
  client.println(rev);
  client.println(F("</h4>"));

  client.println(F("</body>"));
  client.println(F("</html>"));


  return(0);
}
void getTimePrintOut(unsigned long millisnbr,char *buf) {
char tmpbuf[40];
strcpy(buf,"");
unsigned long tmpmillins=millisnbr;
//
//          /* 4 is mininum width, 2 is precision; float value is copied onto str_temp*/
//dtostrf(_timeLeftMin, 6, 2, strbuf);


unsigned long tmphours = millisnbr / 3600000;
unsigned long tmphours_remain = millisnbr % 3600000;
tmpmillins = tmpmillins - (tmphours * 3600000);

unsigned long tmpmin = tmpmillins / 60000;
unsigned long tmpmin_remain = tmpmillins % 60000;
tmpmillins = tmpmillins - (tmpmin * 60000);

unsigned long tmpsec = tmpmillins / 1000;
unsigned long tmpsec_remain = tmpmillins % 1000;
tmpmillins = tmpmillins - (tmpsec * 1000);

if (tmphours>0) {
  sprintf(tmpbuf,"%luh ",tmphours);
  strcat(buf,tmpbuf);
} 
if (tmpmin>0) {
  sprintf(tmpbuf,"%02lum ",tmpmin);
  strcat(buf,tmpbuf);
}
if (tmpsec>0 && tmphours==0) {
  sprintf(tmpbuf,"%02lus ",tmpsec);
  strcat(buf,tmpbuf);
}

}


////////////////////////////////////////////////////////////////////////
//htmlFooter Function
////////////////////////////////////////////////////////////////////////
//Prints html footer
void printHtmlFooter(EthernetClient client){
    //Set Variables Before Exiting 
    printLastCommandOnce = false;

    delay(10); // give the web browser time to receive the data
    client.stop(); // close the connection:
    if (DEBUGLEVEL>8) {Serial.println(F(" - Done, Closing Connection.")); }
    
    delay (100); //delay so that it will give time for client buffer to clear and does not repeat multiple pages.
    
 } //end of htmlFooter


////////////////////////////////////////////////////////////////////////
//triggerPin Function
////////////////////////////////////////////////////////////////////////
// 
void triggerPin(int swi,  int setpin){
  //Switching on or off outputs, reads the outputs and prints the buttons   

  //Setting Outputs
 
//Code stupide ! Needs to be fixed
    if(setpin == HIGH) {
      if (outputInverted[swi]){ 
        digitalWrite(outputAddress[swi], LOW);
      } 
      else{
        digitalWrite(outputAddress[swi], HIGH);
      }
    }
    if(setpin == LOW){
      if (outputInverted[swi] ){ 
        digitalWrite(outputAddress[swi], HIGH);
      } 
      else{
        digitalWrite(outputAddress[swi], LOW);
      }
    }

}

void initDigPin() {
  if (relayTestMode == true){
    Serial.println(F("**************Test Relay DIG Pin**********************"));
  } else {
    Serial.println();
  }
  pinMode(LED_STATUS_ZONE1_DIGITAL_OUT, OUTPUT);


  //Digital Relay on board
  for (int i=0;i<NBR_RELAY_INSTALLED;i++) {
    pinMode(outputAddress[i], OUTPUT);
  }

  for (int i=0;i<NBR_RELAY_INSTALLED;i++) {
    Serial.print(F("Relay "));
    Serial.print(i+1);
    Serial.print(F(" Digital On-Board OUT: "));
    Serial.println(outputAddress[i]);
    triggerPin(i,_default_On_Off[i]);
    if (relayTestMode == true){
      delay (500);
      triggerPin(i,HIGH);
      digitalWrite(LED_STATUS_ZONE1_DIGITAL_OUT, HIGH);
      delay(1000);
      triggerPin(i,LOW);
      digitalWrite(LED_STATUS_ZONE1_DIGITAL_OUT, LOW);
    }
  }
  if (relayTestMode == true){
    Serial.println(F("*************************************************"));
  } 
}

// Process timers
void processTimers () {
  char buf[256];
  for (int i=0;i<NUM_SWITCH;i++) {
      if (_timer_status[i]==1) { // Time is on
        _previousMillis[i]=_currentMillis[i];
        _currentMillis[i]=millis();
        if (_previousMillis > _currentMillis) { //50 days reset of board time!
          _currentMillis[i]=millis();
          _previousMillis[i]=millis();
        }
        unsigned long tmpmillis=_currentMillis[i]-_previousMillis[i];
        if (tmpmillis>_timeLeftMillis[i]) {
          _timeLeftMillis[i]=0;
        } else {
          _timeLeftMillis[i] = _timeLeftMillis[i] - tmpmillis;
        }

    
        long next_choice_available_millis=TIME_YOU_HAVE_TO_MAKE_A_CHOICE; //Give 1min to switch to next option !
        if (TIMELEFTDEFAULT<TIME_YOU_HAVE_TO_MAKE_A_CHOICE) { //This IF in case we are in test mode !
          next_choice_available_millis=long(TIMELEFTDEFAULT/3);
        }
        if (_duration_choices[i] >= 1 && 
            _timeLeftMillis[i] < (_duration_available[_duration_choices[i]] ) - next_choice_available_millis) {
          Serial.println(F("**************************************"));
          Serial.println(millis());
          Serial.print(F("Decrease Duration choice swi#"));
          Serial.print(i);
          Serial.print(F(" from '"));
          Serial.print(_duration_choices[i]);
          _duration_choices[i] = _duration_choices[i] - 1;
          Serial.print(F("' to '"));
          Serial.print(_duration_choices[i]);
          Serial.print(F("'  _timeLeftMillis[i]=")); 
          Serial.print(_timeLeftMillis[i]);
          Serial.print(F("_duration_available[_duration_choices[i]-1]="));
          Serial.print(_duration_available[_duration_choices[i]-1]);
          Serial.println(F(")"));
        }
        
        if (_timeLeftMillis[i]<=0) {
          sprintf(buf,"Timer#%d Expired: _timeLeftMillis[%d]=%lu, _currentMillis[%d]=%lu, _previousMillis[%d]=%lu",
                  i,i,_timeLeftMillis[i],i,_currentMillis[i],i,_previousMillis[i]);
          Serial.println(buf);
          _timeLeftMillis[i]=0;
          _currentMillis[i]=millis();
          _previousMillis[i]=millis();
         _timer_status[i]=TIMER_EXPIRED; //Timer Expired      
        }
      } // if time status =1

      if (_timer_status[i]==TIMER_EXPIRED) { // Time expired
        _currentMillis[i]=millis();
        _previousMillis[i]=millis();
        _timeLeftMillis[i]=0;
        _timer_status[i]=0; //reset !
        on_off[i]=_default_On_Off[i];
        triggerPin(i,_default_On_Off[i]);
      _duration_choices[i]=0; //reset
      }


      
      if (DEBUGLEVEL >=6 ){ // ((_timeLeftMillis[i]%5)==0) ) {
        sprintf(buf,"processTimers Millis stus[%d]=%d, timeLeft[%d]=%lu, current[%d]=%lu, previous[%d]=%lu",
                i,_timer_status[i],i,_timeLeftMillis[i],i,_currentMillis[i],i,_previousMillis[i]);
        Serial.println(buf);
      }
  }
}

// Init Arrays General (Timers...)
void initArrays() {
  for (int i=0;i<NUM_SWITCH;i++) {
    _currentMillis[i]=millis();
    _previousMillis[i]=millis();
    _timeLeftMillis[i]=0;
    _timer_status[i]=0;
    on_off[i]=_default_On_Off[i];
    _duration_choices[i]=0; //_duration_available[0] //ON default
  }
  
}

//////////////////////////////////////////////////////////////////////
//readOutputStatuses Function
//////////////////////////////////////////////////////////////////////
//Reading the Output Statuses
void readOutputStatuses(){

  if (DEBUGLEVEL > 5) {
    Serial.print(F("** Digital Output ** "));
    for (int swi = 0; swi < NBR_RELAY_INSTALLED; swi++)  { 
      Serial.print(F("Digital Output "));
      Serial.print(outputAddress[swi]);
      Serial.print(F(" Status: "));
      Serial.println(digitalRead(outputAddress[swi]));
    }
  }

}

//////////////////////////////////////////////////////////////////////
void printpCounter() {
  pcounter++;
  if(DEBUGLEVEL>6) {
    Serial.print("pcounter=");
    Serial.println(pcounter);
  }
}
//////////////////////////////////////////////////////////////////////

//////////////////////////////////////////////////////////////////////
// Read Temperaure Sensor
int readTempDHT21() {
  // READ DATA
  double DHT21_temp=-2000;
  double DHT21_hum=150;
  
  //Serial.print("DHT21, \t");
  int chk = DHT21.read21(DHT21_PIN);
  switch (chk)
  {
    case DHTLIB_OK:  
    if (DEBUGLEVEL>5) {
      Serial.println(F("DHT21 OK!")); 
    }
    DHT21_temp=DHT21.temperature;
    DHT21_hum=DHT21.humidity;

    
    break;
    case DHTLIB_ERROR_CHECKSUM: 
    Serial.println(F("DHT21 Checksum error!")); 
    break;
    case DHTLIB_ERROR_TIMEOUT: 
    Serial.println(F("DHT21 Time out error!")); 
    break;
    default: 
    Serial.println(F("DHT21 Unknown error!")); 
    break;
  }
  // DISPLAY DATA

  if (DEBUGLEVEL>2) { 
    Serial.print(F("Temp/Hum: "));
    Serial.print(DHT21_temp,1);
    Serial.print("/");
    Serial.println(DHT21_hum,1);
  }
  _DHT21_TEMP_HUM[0]=DHT21_temp;
  _DHT21_TEMP_HUM[1]=DHT21_hum;
  return chk;
}

//////////////////////////////////////////////////////////////////////
//  Turn on LED for ZOne defined by ZONE_FOR_DURATION_CHOICE_LED_STATUS when
// active.
//////////////////////////////////////////////////////////////////////
void durationChoicesAnalogPins () {

    if (_duration_choices[ZONE_FOR_DURATION_CHOICE_LED_STATUS] >= 1) {
        digitalWrite(LED_STATUS_ZONE1_DIGITAL_OUT, HIGH);
    } else {
        digitalWrite(LED_STATUS_ZONE1_DIGITAL_OUT, LOW);
    }

}

//////////////////////////////////////////////////////////////////////
// Check Button Analog Input#0 to click on switch on/off in lieu 
// of web interface on ZONE_FOR_DURATION_CHOICE_LED_STATUS
//////////////////////////////////////////////////////////////////////
boolean checkButtonAnalog () {

  byte val = analogRead(PUSH_BUTTON_ANALOG_IN);    // read the input pin
  byte setpin = LOW;
  byte swi=ZONE_FOR_DURATION_CHOICE_LED_STATUS;
  int ledflashdelay=100;

  if (val >= PUSHBUTTON_PRESS_LEVEL_SENSITIVITY) {  //val =0 1-254 if not grounded !  when not pressed. 255 when button pressed with perfect connection!
    _led_flash_time_interval=millis();  
    if (_duration_choices[swi]< (NBR_DURATIONS_CHOICES-1)) {
      setpin=HIGH;
    } else {
      setpin=LOW;
    }
    int tmp_next_choice=0;
    on_off[swi]=setpin;
    triggerPin(swi,setpin);
    //devrait combine ce code avec process command !
    if (setpin==_default_On_Off[swi]) { 
      _timeLeftMillis[swi]=0;
      _timer_status[swi]=TIMER_OFF; //Timer Off
      _duration_choices[swi]=0; //reset
    } else {
        _timer_status[swi]=TIMER_ON; //Timer ON    
        _currentMillis[swi]=millis();
        _previousMillis[swi]=millis(); 
        //duration_choices[i]
        tmp_next_choice=_duration_choices[swi]+1;
        if (tmp_next_choice>=NBR_DURATIONS_CHOICES) {
          // Next choice is 0
          _duration_choices[swi]=0;
        } else {
          // A few off choices
          _duration_choices[swi]=tmp_next_choice;
        }
        _timeLeftMillis[swi]=_duration_available[tmp_next_choice];
        _duration_choices[swi]=tmp_next_choice;
    }
    if (DEBUGLEVEL >2) {
      Serial.print(F("Button pressed.  Duration next_choice=")); 
      Serial.println(tmp_next_choice);
    }
    delay(400);
  } else { // val button NOT pressed
    if (millis() > (_led_flash_time_interval + 3000)){ 
      readOutputStatuses();
      _led_flash_time_interval=millis();  
      //_duration_available
      int ledloop=0;
      if (_timeLeftMillis[swi] >1000) {
        for (int da=0;da<NBR_DURATIONS_CHOICES;da++) {
          if (_timeLeftMillis[ZONE_FOR_DURATION_CHOICE_LED_STATUS] > _duration_available[da]) {
              ledloop++; //Do at least one loop
          } else {
            da=NBR_DURATIONS_CHOICES; //exist loop
          }
        }
      }      
      for (int i=0;i<ledloop;i++) {
        digitalWrite(LED_STATUS_ZONE1_DIGITAL_OUT, LOW);
        delay (int(ledflashdelay/ledloop));
        digitalWrite(LED_STATUS_ZONE1_DIGITAL_OUT, HIGH);
        delay (int(ledflashdelay/ledloop));
      }
          //delay (int(ledflashdelay));
      }
    if (DEBUGLEVEL>2) {
      if (val >0 || DEBUGLEVEL >5) {
        Serial.print(F("Button Input value Analog Port:")); 
        Serial.println(val);
      }   
    }          // debug value

  
  }
}







