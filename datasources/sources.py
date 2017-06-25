import logging
from multiprocessing import Lock

import MySQLdb
from decouple import config
from jira.client import JIRA
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sugarutils import LiteSugarCRM

logger = logging.getLogger(__name__)


class DataSource(object):
    """
    Semi-singleton data source object protected with Mutex for thread safety
    """
    __mutex__ = Lock()

    def __init__(self):
        self._instance = None

    @property
    def instance(self):
        """
        Returns instance of creates a new one
        :return: DataSource instance
        """
        self.__mutex__.acquire()
        try:
            if self._instance is None:
                self._instance = self.init_instance()
            return self._instance
        finally:
            self.__mutex__.release()

    def init_instance(self):
        """
        Abstract method for creating DataSource instance
        :return: New DataSource instance object
        """
        pass


class DefaultJiraSource(DataSource):
    def init_instance(self):
        jira_opts = {'server': config('JIRA_URL')}
        jira_auth = (config('JIRA_USER'), config('JIRA_PASS'))
        logging.info("Configuring JIRA %s@%s", config('JIRA_USER'), config('JIRA_URL'))
        return JIRA(options=jira_opts, basic_auth=jira_auth)


class DefaultSugarSource(DataSource):
    def init_instance(self):
        sugar_user = config('SUGAR_USER')
        sugar_pass = config('SUGAR_PASS')
        sugar_rest = config('SUGAR_REST')
        logging.info("Configuring SugarCRM user=%s at REST=%s", sugar_user, sugar_rest)
        return LiteSugarCRM(user=sugar_user, passwd=sugar_pass, rest=sugar_rest)


class DefaultSQLDataSource(DataSource):
    def __init__(self, creator=None):
        self._creator = creator
        super(DefaultSQLDataSource, self).__init__()

    def init_instance(self):
        logger.info("Configuring ORM for {}".format(config('DB_ENGINE')))
        db = create_engine(config('DB_ENGINE') + "://", creator=self._creator)
        maker = sessionmaker(bind=db, autoflush=False)
        return maker()

    def set_creator(self, func):
        """
        Bind creator function (sqlalchemy specific) to create DB connection
        :param func:
        :return:
        """
        self._creator = func


def mysql_creator():
    """
    Default MYSQL creator function for DefaultSQLDataSource
    :return: function
    """
    mysql_user = config('MYSQL_USER')
    mysql_pass = config('MYSQL_PASS')
    mysql_host = config('MYSQL_HOST')
    mysql_port = config('MYSQL_PORT', default=3306, cast=int)
    mysql_charset = config('MYSQL_CHARSET', default='utf8')
    mysql_db = config('MYSQL_DB')

    logger.info("Injecting MYSQL connection {}@{}:{}/{}".format(mysql_user, mysql_host, mysql_port, mysql_db))
    logger.info("MYSQL-Encoding: {}".format(mysql_charset))
    return MySQLdb.connect(user=mysql_user, host=mysql_host, port=mysql_port, db=mysql_db, charset=mysql_charset,
                           passwd=mysql_pass)


JiraSource = DefaultJiraSource()
SugarSource = DefaultSugarSource()
SQLDataSource = DefaultSQLDataSource()
