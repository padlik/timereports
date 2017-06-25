import logging
import signal
import sys
import threading
import time

from decouple import config

from datasources import SQLDataSource, mysql_creator
from payloads import JiraPayload, SugarPayload2, GooglePayload

logger = logging.getLogger(__name__)

__INTERVAL__ = config('RUN_INTERVAL', default=300, cast=int)


class RunThread(threading.Thread):
    def __init__(self, event, payloads=None):
        threading.Thread.__init__(self)
        if payloads is None:
            payloads = []
        logger.info("About to start working thread")
        self.stopped = event
        self.payloads = payloads
        self._attempts = 0

    def run(self):
        logger.info("Entering running function")
        attempts = 0
        uptime = time.time()
        while self.stopped.is_set():
            logger.info("Worker thread wake up call")
            attempts += 1
            logger.info("Iteration #{} uptime: {} sec.".format(attempts, time.time() - uptime))
            if self.payloads:
                for p in self.payloads:
                    start_time = time.time()
                    logger.info("Starting payload {}".format(str(p)))
                    if self.stopped.is_set():
                        try:
                            p.payload()
                            logger.info("Payload finished in : {} seconds".format(time.time() - start_time))
                        except Exception as e:
                            logger.warn('Exception in Payload {}:{}'.format(p, e.message))
                            logger.warn('Trying to continue to the next Payload')
                    else:
                        logger.info("Stop signal received. Stopping gracefully...")
            else:
                logger.info("Empty payload list, consider to stop this thread")

            if self.stopped.is_set():
                logger.info("Worker thread asleep for {} seconds".format(__INTERVAL__))
                n = int(round(float(__INTERVAL__) / float(10)))
                for n in reversed(xrange(n)):
                    logger.info("Restart in {} seconds".format(n * 10))
                    time.sleep(10)
                    if not self.stopped.is_set():
                        break


def init_logging():
    log_level = logging.DEBUG if config('DEBUG', cast=bool) else logging.INFO
    logging.basicConfig(level=logging.INFO,
                        format="[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
                        datefmt="%H:%M:%S")
    if log_level == logging.DEBUG:
        logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)


if __name__ == "__main__":

    init_logging()

    stopFlag = threading.Event()
    stopFlag.set()

    # configure ORM with MySQL
    SQLDataSource.set_creator(mysql_creator)

    sugar_payload = SugarPayload2()
    jira_payload = JiraPayload()
    google_payload = GooglePayload()

    thread = RunThread(stopFlag, [sugar_payload, jira_payload, google_payload])
    # thread = RunThread(stopFlag, [google_payload])
    # thread = RunThread(stopFlag, [sugar_payload])
    thread.start()


    def sigterm_handler(signum, frame):
        logger.warn("SIGTERM caught ({}), stopping...".format(signum))
        stopFlag.clear()
        raise KeyboardInterrupt


    signal.signal(signal.SIGTERM, sigterm_handler)

    try:
        while 1:
            time.sleep(.1)
    except KeyboardInterrupt:
        logger.warn("Keyboard Interrupt: Gracefully stopping. Please wait...")
        stopFlag.clear()
        thread.join()
        sys.exit(0)
