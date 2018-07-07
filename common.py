import logging, sys
import configparser
import threading

config = configparser.ConfigParser(allow_no_value=True)
config.read('main.conf')

#notifying phone numbers
nums = []
for number in config['NUMBERS']: nums.append(number)
NOTIFY_GSM_NUMBERS = tuple(nums)

#retry attempts
REDIAL_COUNT = config['CALL']['Redials']

#notification settings
NOTIFY_GAP = config['NOTIFICATIONS']['NotifyGap']

#meye nvr server info
NVR_SERVER_MAC_ADDRESS = config['SERVER']['ServerMAC']
NVR_SERVER_IP_ADDRESS = config['SERVER']['ServerIP']
NVR_SERVER_PORT = config['SERVER']['ServerPort']

homeSecurityLogger = logging.getLogger('MAINLOG')
handler=logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter("%(asctime)s %(filename)-12.12s %(levelname)-8s: %(message)s"))
homeSecurityLogger.addHandler(handler)
homeSecurityLogger.setLevel(logging.DEBUG)


#named pipe for IPC
FIFO = 'homesecpipe'

#ports
WEBSERVER_PORT=9090

#some IPC commands
MOTION_DETECTED_COMMAND = 'MOTIONDETECT'
WEBSERVER_READY_COMMAND = 'HTTPREADY'
WEBSERVER_FAIL_COMMAND = 'HTTPFAIL'

#kill flag. once set, all processes and threads should respect it and gracefully terminate
KILL_FLAG = False

