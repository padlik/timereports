import logging
import signal
import sys
import threading
import time

from decouple import config

from datasources import SQLDataSource, postgres_creator
from payloads import SugarPayload, JiraPayload, GooglePayload

logger = logging.getLogger(__name__)

__INTERVAL__ = config('RUN_INTERVAL', default=300, cast=int)
__PAYLOADS__ = [SugarPayload, JiraPayload, GooglePayload]  # Payload order is important
__VERSION__ = "2.0 Postgres; SQLAlchemy; Heroku; Sugar Rest v11"


class RunThread(threading.Thread):
    def __init__(self, event, payloads=None):
        threading.Thread.__init__(self)
        if payloads is None:
            payloads = []
        logger.info("About to start working thread")
        logger.info("==Application version: {}".format(__VERSION__))
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
            logger.info("===== Iteration #{} uptime: {} sec. =====".format(attempts, time.time() - uptime))
            if self.payloads:
                for p in self.payloads:
                    start_time = time.time()
                    logger.info("Starting payload {}".format(str(p)))
                    if self.stopped.is_set():
                        try:
                            p.payload()
                            logger.info("Payload finished in : {} seconds".format(time.time() - start_time))
                        except Exception as e:
                            logger.warning('Exception in Payload {}:{}'.format(p, e))
                            logger.warning('Trying to continue to the next Payload')
                    else:
                        logger.info("Stop signal received. Stopping gracefully...")
            else:
                logger.info("Empty payload list, consider to stop this thread")

            logger.info('===== Finished attempt #{} ====='.format(attempts))
            if self.stopped.is_set():
                logger.info("Worker thread asleep for {} seconds".format(__INTERVAL__))
                for _ in reversed(range(int(round(float(__INTERVAL__) / float(10))))):
                    time.sleep(10)
                    if not self.stopped.is_set():
                        break


def init_logging():
    log_level = logging.DEBUG if config('DEBUG', cast=bool) else logging.INFO
    logging.basicConfig(level=log_level,
                        format="[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
                        datefmt="%H:%M:%S")

    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)

    if log_level == logging.DEBUG:
        logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
        logging.getLogger('urllib3').setLevel(logging.INFO)


if __name__ == "__main__":

    init_logging()

    stopFlag = threading.Event()
    stopFlag.set()

    # configure ORM with MySQL
    # SQLDataSource.set_creator(mysql_creator)
    SQLDataSource.set_creator(postgres_creator)

    # Init all payloads
    payloads_init = []
    for payload in __PAYLOADS__:
        p = payload()
        payloads_init.append(p)

    thread = RunThread(stopFlag, payloads_init)
    thread.start()


    def sigterm_handler(signum, _):
        logger.warning("SIGTERM caught ({}), stopping...".format(signum))
        stopFlag.clear()
        raise KeyboardInterrupt


    signal.signal(signal.SIGTERM, sigterm_handler)

    try:
        while 1:
            time.sleep(.1)
    except KeyboardInterrupt:
        logger.warning("Keyboard Interrupt: Gracefully stopping. Please wait...")
        stopFlag.clear()
        thread.join()
        sys.exit(0)
