import logging, sys
import configparser

config = configparser.ConfigParser(allow_no_value=True)
config.read('main.conf')

#notifying phone numbers
nums = []
for number in config['NUMBERS']: nums.append(number)
NOTIFY_GSM_NUMBERS = tuple(nums)

#retry attempts
REDIAL_COUNT = config['CALL']['Redials']

homeSecurityLogger = logging.getLogger('MAINLOG')
handler=logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter("%(asctime)s %(filename)-12.12s %(levelname)-8s: %(message)s"))
homeSecurityLogger.addHandler(handler)
homeSecurityLogger.setLevel(logging.DEBUG)


#named pipe for IPC
FIFO = 'homesecpipe'


#motion detected IPC command
MOTION_DETECTED_COMMAND = 'MOTIONDETECT'
