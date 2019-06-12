# home-security

This repository houses the Raspberry Pi based Home Security communication solution. 
The software is deployed on a raspberry pi connected via serial por to a SIM800 GSM module hat that provides telecommunications.

Features
1. Receive web requests from cameras when motion is detected.
2. Place GSM calls to predefined phone numbers upon motion detection and monitor call state. Redial a specified number of times if call was not connected or try a different number
3. Send an SMS message to predefined phone numbers if call was not connected after all redial attempts
4. Receive and react to SMS messages 
5. Monitor connection to Network Video Recorder (Laptop running Linux). If offline send Wake-On-LAN packets to switch on the server (say after power loss)
