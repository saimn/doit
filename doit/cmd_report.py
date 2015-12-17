from collections import defaultdict
from .cmd_base import DoitCmdBase
from .cmd_base import subtasks_iter

opt_html = {
    'name': 'html',
    'short': '',
    'long': 'html',
    'type': str,
    'default': None,
    'help': "Filename to save HTML report"
    }


class Report(DoitCmdBase):
    name = "report"
    doc_purpose = "Reports the status of tasks and subtasks"
    doc_usage = ""
    cmd_options = (opt_html, )
    doc_description = """
"""

    def _execute(self, html=None, pos_args=None):
        from astropy.table import Table
        # dict of all tasks
        tasks = dict([(t.name, t) for t in self.task_list])
        task_list = self.task_list
        stat = {}

        for task in task_list:
            if task.has_subtask:
                stat[task.name] = d = defaultdict(int)
                for subtask in subtasks_iter(tasks, task):
                    res = self.dep_manager.get_status(subtask, tasks)
                    d[res.status] += 1
                d['total'] = sum(d.values())

        states = ['run', 'error', 'up-to-date', 'total']
        cols = [stat.keys()]
        for state in states:
            cols.append([stat[name][state] for name in cols[0]])
        cols.append([tasks[name].doc for name in cols[0]])

        t = Table(cols, names=['name'] + states + ['doc'])
        self.outstream.write(t)

        if html:
            t.write(html, format='jsviewer')

        self.dep_manager.close()
