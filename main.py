
#This is meant to be the middleman between the sim800 and the motion detection
import os, subprocess
import errno
import sim800 

#project imports
import common

FIFO = common.FIFO
logger = common.homeSecurityLogger

try:
    os.mkfifo(FIFO)
except OSError as oe: 
    if oe.errno != errno.EEXIST:
        raise

logger.debug("Starting main daemon...")
gsm = sim800.SMS(sim800.PORT, sim800.BAUD, logger)
gsm.setup()
if not gsm.turnOn(): exit(1)
if not gsm.setEchoOff: exit(1)
logger.info("GSM module set up successfully")

logger.debug("Starting web server in subprocess")
cmd = ['./web-server.py']
process = subprocess.Popen(cmd)

logger.debug("Starting mainloop for reading IPC pipe")
try:
    while True:
        logger.debug("Opening FIFO pipe and waiting for data...")
        with open(FIFO) as fifo:
            logger.debug("FIFO opened. Receiving data...")
            while True:
                data = fifo.read()
                if len(data) == 0: break
                logger.debug('IPC data received: "{0}"'.format(data))
                if(data == 'TEST'):
                    gsm.placeCall(common.NOTIFY_GSM_NUMBER)
except KeyboardInterrupt:
    print("")
    pass

#attempt deleting of pipe
try:
    os.remove(FIFO)
    logger.debug("FIFO pipe deleted")
except (OSError, e):  ## if failed, report it back to the user ##
    logger.error("Failed to delete pipe. Error: %s." % (e.strerror))

