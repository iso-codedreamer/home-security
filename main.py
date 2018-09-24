#!/usr/bin/python3

import os, subprocess
import atexit
import types
import threading
import time
import signal

#project imports
import common
import sim800 

FIFO = common.FIFO
logger = common.homeSecurityLogger
gsmLock = threading.Lock()

def handle_sigterm(a, b):
    logger.info("Received SIGTERM. Performing cleanup...")
    common.KILL_FLAG = True
    gsm.interruptMTDataWait()
    exit(0)

@atexit.register
def exit_handler():
    logger.info("Received exit code")
    #kill subrocesses that are still running
    killsubprocesses = ({"process":httpprocess, "name":"web server"},{"process":watchdogprocess, "name":"NVR watchdog"})
    killtimeout = 3
    for item in killsubprocesses:
        processname = item["name"]
        killprocess = item["process"]
        if isinstance(killprocess, subprocess.Popen):
            if killprocess.poll() is None:
                logger.debug("Terminating {} subprocess".format(processname))
                killprocess.terminate()
                try:
                   killprocess.wait(killtimeout)
                except subprocess.TimeoutExpired:
                    logger.warning("{} subprocess did not terminate within {} seconds".format(processname, killtimeout))
                else:
                    logger.info("{} terminated successfully".format(processname))
            else:
                logger.info("{} process is already dead".format(processname))

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
    gsm.interruptMTDataWait()
    with gsmLock:
        logger.debug("{} acquired GSM lock".format(threading.current_thread().name))
        logger.debug("Handling motion detection event")
        notifyComplete = False
        for number in common.NOTIFY_GSM_NUMBERS:
            attempt = 1
            while attempt <= int(common.REDIAL_COUNT)+1 and not common.KILL_FLAG:
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

def handleMTMessage(message):
    message = message.upper()
    if message == "RING":
        gsm.handleIncomingCall(common.NOTIFY_GSM_NUMBERS)

def readFIFO():
    with open(FIFO) as fifo:
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

class MTDataWaitingThread (threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        logger.debug("Started MT data waiting thread {}".format(self.name))
        with gsmLock:
            logger.debug("{} acquired GSM lock".format(self.name))
            data = gsm.awaitDataFromMT() 
            if data is not None: handleMTMessage(data)
        logger.debug("{} has finished".format(self.name))
        if not common.KILL_FLAG:
            time.sleep(.5) #a little spacing before we attempt reentering the mode
            nextWaitingThread = MTDataWaitingThread()
            nextWaitingThread.start()


signal.signal(signal.SIGTERM, handle_sigterm)
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
gsm.deleteAllSMS()

logger.debug("Starting web server in subprocess and waiting for ready message")
cmd = ['./web-server.py']
httpprocess = subprocess.Popen(cmd)
status = readFIFO()
if status == common.WEBSERVER_READY_COMMAND:
    logger.info("Web server subprocess reported ready")
elif status == common.WEBSERVER_FAIL_COMMAND:
    logger.critical("Web server subprocess reported failure. Script has to exit")
    exit(1)

logger.debug("Starting nvr server watchdog in subprocess")
cmd = ['./nvr-watchdog.py']
watchdogprocess = subprocess.Popen(cmd)

mtDataThread = MTDataWaitingThread()
mtDataThread.start()

logger.debug("Starting mainloop for reading IPC pipe")
try:
    while True:
        data = readFIFO()
        if data == common.MOTION_DETECTED_COMMAND:
            thread = SIM800Thread(handleMotionDetection)
            thread.start()
except KeyboardInterrupt:
    print("")
    common.KILL_FLAG = True
    gsm.interruptMTDataWait()

