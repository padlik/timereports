import signal
import sys
import threading
import time

from decouple import config

from payloads import JiraPayload, SugarPayload, GooglePayload
from primitives import Logger, set_logging

__INTERVAL__ = config('RUN_INTERVAL', default=300, cast=int)


class RunThread(threading.Thread):
    def __init__(self, event, payloads=None):
        threading.Thread.__init__(self)
        if payloads is None:
            payloads = []
        Logger.info("About to start working thread")
        self.stopped = event
        self.payloads = payloads

    def run(self):
        Logger.info("Entering running function")
        while self.stopped.is_set():
            Logger.info("Worker thread wake up call")
            if self.payloads:
                for p in self.payloads:
                    start_time = time.time()
                    Logger.info("Starting payload {}".format(str(p)))
                    if self.stopped.is_set():
                        p.payload()
                        Logger.info("Payload finished in : {} seconds".format(time.time() - start_time))
                    else:
                        Logger.info("Stop signal received. Stopping gracefully...")
            else:
                Logger.info("Empty payload list, consider to stop this thread")

            if self.stopped.is_set():
                Logger.info("Worker thread asleep for {} seconds".format(__INTERVAL__))
                n = int(round(float(__INTERVAL__) / float(10)))
                for n in reversed(xrange(n)):
                    Logger.info("Restart in {} seconds".format(n * 10))
                    time.sleep(10)
                    if not self.stopped.is_set():
                        break


def config_injectors():
    from reports import inject, litesugarcrm
    from reports.injectors import SugarDb, SQLDb, Jira
    import MySQLdb
    from jira.client import JIRA

    sugar_user = config('SUGAR_USER')
    sugar_pass = config('SUGAR_PASS')
    sugar_rest = config('SUGAR_REST')
    Logger.info("Injecting SugarCRM user={} at REST={}".format(sugar_user, sugar_rest))
    sugarcrm = litesugarcrm.LiteSugarCRM(user=sugar_user, passwd=sugar_pass, rest=sugar_rest)

    mysql_user = config('MYSQL_USER')
    mysql_pass = config('MYSQL_PASS')
    mysql_host = config('MYSQL_HOST')
    mysql_port = config('MYSQL_PORT', default=3306, cast=int)
    mysql_charset = config('MYSQL_CHARSET', default='utf8')
    mysql_db = config('MYSQL_DB')

    Logger.info("Injecting MYSQL connection {}@{}:{}/{}".format(mysql_user, mysql_host, mysql_port, mysql_db))
    Logger.info("MYSQL-Encoding: {}".format(mysql_charset))
    sqldb = MySQLdb.connect(user=mysql_user, host=mysql_host, port=mysql_port, db=mysql_db, charset=mysql_charset,
                            passwd=mysql_pass)

    jira_opts = {'server': config('JIRA_URL')}
    jira_auth = (config('JIRA_USER'), config('JIRA_PASS'))
    Logger.info("Injecting JIRA {}@{}".format(config('JIRA_USER'), config('JIRA_URL')))
    jira = JIRA(options=jira_opts, basic_auth=jira_auth)

    def injector_config(binder):
        binder.bind(SugarDb, sugarcrm)
        binder.bind(SQLDb, sqldb)
        binder.bind(Jira, jira)

    inject.configure(injector_config)
    Logger.info("Injection actions are completed")
    Logger.info("")


if __name__ == "__main__":
    set_logging({'debug': config('DEBUG', cast=bool)})
    stopFlag = threading.Event()
    stopFlag.set()
    config_injectors()
    sugar_payload = SugarPayload(config('REPO_YEAR', cast=int, default=2017), config('REPO_MONTH', cast=int, default=4))
    jira_payload = JiraPayload(config('REPO_YEAR', cast=int, default=2017), config('REPO_MONTH', cast=int, default=4),
                               config('JIRA_THREADS', cast=int))
    google_payload = GooglePayload(config('GOOGLE_SHEET'), config('REPO_YEAR', cast=int, default=2017),
                                   config('REPO_MONTH', cast=int, default=4))
    thread = RunThread(stopFlag, [sugar_payload, jira_payload, google_payload])
    thread.start()


    def sigterm_handler(signum, frame):
        Logger.warn("SIGTERM caught ({}), stopping...".format(signum))
        stopFlag.clear()
        raise KeyboardInterrupt


    signal.signal(signal.SIGTERM, sigterm_handler)

    try:
        while 1:
            time.sleep(.1)
    except KeyboardInterrupt:
        Logger.warn("About to exit")
        stopFlag.clear()
        thread.join()
        sys.exit(0)
