import logging

from jira.client import JIRA

from sugarutils import LiteSugarCRM

log = logging.getLogger(__name__)


class ExtDataSourceFactory(object):
    def __init__(self):
        self._instance = None
        self._config = None

    @property
    def instance(self):
        if self._instance is None:
            self._instance = self.connect()
        return self._instance

    def connect(self):
        pass


class JiraSourceFactory(ExtDataSourceFactory):
    def connect(self):
        jira_opts = {'server': self._config('JIRA_URL')}
        jira_auth = (self._config('JIRA_USER'), self._config('JIRA_PASS'))
        log.info("Injecting JIRA %s@%s", self._config('JIRA_USER'), self._config('JIRA_URL'))
        return JIRA(options=jira_opts, basic_auth=jira_auth)


class SugarSourceFactory(ExtDataSourceFactory):
    def connect(self):
        sugar_user = self._config('SUGAR_USER')
        sugar_pass = self._config('SUGAR_PASS')
        sugar_rest = self._config('SUGAR_REST')
        log.info("Injecting SugarCRM user=%s at REST=%s", sugar_user, sugar_rest)
        return LiteSugarCRM(user=sugar_user, passwd=sugar_pass, rest=sugar_rest)


JiraSource = JiraSourceFactory()
SugarSource = SugarSourceFactory()


def connect_config(newconfig):
    JiraSource._config = newconfig
    SugarSource._config = newconfig
