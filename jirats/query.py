__author__ = 'paul'

from timesheet import TimeSheet


class JiraQuery(object):
    """
         Jira timesheets query class
    """

    _q = 'key in workedIssues("{start}", "{finish}", "{user}")'

    def __init__(self, auth_jira_client):
        self._jira = auth_jira_client

    def get_sheets(self, start_date, finish_date, user):
        """
        :param start_date: Start date of a range
        :param finish_date: End date of a range
        :param user: user's email
        :return: list of TimeSheet objects
        """

        qry = self._q.format(start=start_date.strftime("%Y/%m/%d"), finish=finish_date.strftime("%Y/%m/%d"), user=user)
        issues = self._jira.search_issues(qry)
        # need to go through all the worklogs of an issue to extract the one belongs to a user
        # apparently this is a crap from JIRA
        ts = []
        for i in issues:
            for w in [w for w in self._jira.worklogs(i.key) if w.author.name == user]:
                if start_date >= w.created <= finish_date:  # it might happens too!
                    ts.append(TimeSheet.make(w.id, w.comment, w.timeSpentSeconds, w.created))
        return ts
