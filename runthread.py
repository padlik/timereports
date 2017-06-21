import logging
import signal
import sys
import threading
import time

from decouple import config

from extsources import connect_config
from payloads import JiraPayload, SugarPayload, GooglePayload

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

    def run(self):
        logger.info("Entering running function")
        while self.stopped.is_set():
            logger.info("Worker thread wake up call")
            if self.payloads:
                for p in self.payloads:
                    start_time = time.time()
                    logger.info("Starting payload {}".format(str(p)))
                    if self.stopped.is_set():
                        p.payload()
                        logger.info("Payload finished in : {} seconds".format(time.time() - start_time))
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


def config_injectors():
    from reports import inject
    from reports.injectors import SQLDb
    import MySQLdb

    mysql_user = config('MYSQL_USER')
    mysql_pass = config('MYSQL_PASS')
    mysql_host = config('MYSQL_HOST')
    mysql_port = config('MYSQL_PORT', default=3306, cast=int)
    mysql_charset = config('MYSQL_CHARSET', default='utf8')
    mysql_db = config('MYSQL_DB')

    logger.info("Injecting MYSQL connection {}@{}:{}/{}".format(mysql_user, mysql_host, mysql_port, mysql_db))
    logger.info("MYSQL-Encoding: {}".format(mysql_charset))
    sqldb = MySQLdb.connect(user=mysql_user, host=mysql_host, port=mysql_port, db=mysql_db, charset=mysql_charset,
                            passwd=mysql_pass)

    def injector_config(binder):
        binder.bind(SQLDb, sqldb)

    inject.configure(injector_config)
    logger.info("Injection actions are completed")
    logger.info("")


if __name__ == "__main__":
    if config('DEBUG', cast=bool):
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    stopFlag = threading.Event()
    stopFlag.set()
    connect_config(config)
    config_injectors()
    sugar_payload = SugarPayload(config('REPO_YEAR', cast=int, default=2017), config('REPO_MONTH', cast=int, default=4))
    jira_payload = JiraPayload(config('REPO_YEAR', cast=int, default=2017), config('REPO_MONTH', cast=int, default=4),
                               config('JIRA_THREADS', cast=int))
    google_payload = GooglePayload(config('GOOGLE_SHEET'), config('REPO_YEAR', cast=int, default=2017),
                                   config('REPO_MONTH', cast=int, default=4))
    thread = RunThread(stopFlag, [sugar_payload, jira_payload, google_payload])
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
        logger.warn("About to exit")
        stopFlag.clear()
        thread.join()
        sys.exit(0)
