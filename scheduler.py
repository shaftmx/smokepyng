

#https://github.com/dbader/schedule/blob/master/schedule/__init__.py

class Scheduler(object):
    def should_run(self):
        """True if the job should be run now."""
        return datetime.datetime.now() >= self.next_run
    def run_pending():
        pass
    def _schedule_next_run(self):
        pass


class Job(object):
    """Describ job name and time to run """

    def __init__(self, name, func, every):
        """
        parameters:
          every : could be in sec or min. example : 10sec or 1min
        """
        self.name = name
        self.func = func
        self.every = every



def foo(num):
    print num

job = Job(name='test')
