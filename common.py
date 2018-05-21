import logging, sys

homeSecurityLogger = logging.getLogger('MAINLOG')
handler=logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter("%(asctime)s %(filename)-12.12s %(levelname)-8s: %(message)s"))
homeSecurityLogger.addHandler(handler)
homeSecurityLogger.setLevel(logging.DEBUG)

#common variables throughout the security system

#named pipe for IPC
FIFO = 'homesecpipe'

#notifying phone number
NOTIFY_GSM_NUMBER = '+255717398906'

