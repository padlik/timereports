__author__ = 'paul'


class TimeSheet(object):
    """ lightweight TimeSheet object. Params is a dictionary of optional values  """
    __slots__ = ('name', 'description', 'time_spent', 'activity_date', 'params')

    def __init__(self):
        self.params = {}

    @staticmethod
    def make(name, description, time_spent, activity_date):
        """
        :param name: Name of a timesheet
        :param description: Description part
        :param time_spent: Time spent in seconds
        :param activity_date: Date of activity
        :return: TimeSheet object
        """
        t = TimeSheet()
        t.name = name
        t.description = description
        t.time_spent = time_spent
        t.activity_date = activity_date
        return t
