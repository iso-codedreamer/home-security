#!/usr/bin/python3

import os, subprocess
import atexit
import types
import threading
import time

#project imports
import common
import sim800 

FIFO = common.FIFO
logger = common.homeSecurityLogger
gsmLock = threading.Lock()

@atexit.register
def exit_handler():
    logger.info("Received exit code")
    #kill subrocesses that are still running
    killtimeout = 3
    if isinstance(httpprocess, subprocess.Popen):
        if httpprocess.poll() is None:
            logger.debug("Terminating web server subprocess")
            httpprocess.terminate()
            try:
               httpprocess.wait(killtimeout)
            except subprocess.TimeoutExpired:
                logger.warning("Webserver subprocess did not terminate within {} seconds".format(killtimeout))
            else:
                logger.info("Webserver terminated successfully")
        else:
            logger.info("Webserver process is already dead")

    #attempt deleting of pipe
    try:
        os.remove(FIFO)
        logger.info("FIFO pipe deleted")
    except OSError:  
        logger.warning("Failed to delete pipe.")


def handleMotionDetection():
    global lastNotifTime
    notifyGapSeconds = float(common.NOTIFY_GAP)*60
    nextNotifTime = lastNotifTime + notifyGapSeconds
    if time.time() < nextNotifTime:
        logger.info("Still within notify gap ({}m). Last event time: {}"
                .format(int(common.NOTIFY_GAP), time.asctime(time.localtime(lastNotifTime))))
        return
    lastNotifTime = time.time()
    gsmLock.acquire()
    logger.debug("{} acquired GSM lock".format(threading.current_thread().name))
    logger.debug("Handling motion detection event")
    notifyComplete = False
    for number in common.NOTIFY_GSM_NUMBERS:
        attempt = 1
        while attempt <= int(common.REDIAL_COUNT)+1:
            logger.debug("Attempt {} for GSM number {}".format(attempt, number))
            callConnected = gsm.placeCall(number)
            if callConnected: 
                notifyComplete = True
                break
            attempt += 1
        if notifyComplete: 
            break
        gsm.sendSMS(number, "Motion detected on {}".format(time.asctime(time.localtime(lastNotifTime))))
    
    logger.info("Event notification complete")
    gsmLock.release()

def readFIFO():
    logger.debug("Opening FIFO pipe and waiting for data...")
    with open(FIFO) as fifo:
        logger.debug("FIFO opened. Receiving data...")
        while True:
            data = fifo.read()
            if len(data) == 0: break
            logger.debug('IPC data received: "{0}"'.format(data))
            return data

class SIM800Thread (threading.Thread):
    def __init__(self, func):
        threading.Thread.__init__(self)
        self.target = func

    def run(self):
        logger.debug("Starting {}".format(self.name))
        self.target()
        logger.debug("{} has finished".format(self.name))


logger.debug("Starting main daemon...")

try:
    os.remove(FIFO)
    logger.debug("A pre-existing FIFO file was removed")
except FileNotFoundError:
    logger.info("Creating new FIFO file")
except OSError:
    logger.critical("Failed to remove pre-existing FIFO file {}".format(FIFO))
    

try:
    os.mkfifo(FIFO)
except OSError as oe: 
    logger.critical("Failed to create {} as FIFO pipe. Error {}. Will terminate".format(FIFO, oe.errno))
    exit(1)

lastNotifTime = 0
gsm = sim800.SMS(sim800.PORT, sim800.BAUD, logger)
gsm.setup()
if not gsm.turnOn(): exit(1)
if not gsm.setEchoOff: exit(1)
logger.info("GSM module set up successfully")

logger.debug("Starting web server in subprocess and waiting for ready message")
cmd = ['./web-server.py']
httpprocess = subprocess.Popen(cmd)
status = readFIFO()
if status == common.WEBSERVER_READY_COMMAND:
    logger.info("Web server subprocess reported ready")
elif status == common.WEBSERVER_FAIL_COMMAND:
    logger.critical("Web server subprocess reported failure. Script has to exit")
    exit(1)

logger.debug("Starting mainloop for reading IPC pipe")
try:
    while True:
        data = readFIFO()
        if data == common.MOTION_DETECTED_COMMAND:
            thread = SIM800Thread(handleMotionDetection)
            thread.start()
except KeyboardInterrupt:
    print("")
    pass

