# -*- coding: utf-8 -*-

from __future__ import division, print_function

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

opt_bar_length = {
    'name': 'bar_length',
    'short': '',
    'long': 'bar-length',
    'type': int,
    'default': 20,
    'help': "Progrees bar length"
    }

BAR_SYMBOL = u'█'

# The background is set with 40 plus the number of the color, and the
# foreground with 30
BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = [
    u'\33[0;%dm' % (40 + i) for i in range(8)]
# These are the sequences need to get colored ouput
RESET_SEQ = u'\033[0m'
BOLD_SEQ = u'\033[1m'


def generate_ascii_bar(stat, bar_length):
    ratio = int(round(stat['up-to-date'] / stat['total'] * bar_length))
    done = ' ' * ratio
    missing = ' ' * (bar_length - ratio)
    done = WHITE + done + RESET_SEQ
    missing = BLACK + missing + RESET_SEQ
    return u'{}{}'.format(done, missing)


# def generate_html_bar(stat, bar_length):
#     ratio = int(round(stat['up-to-date'] / stat['total'] * bar_length))
#     done = 'x' * ratio
#     missing = '.' * (bar_length - ratio)
#     return u'<tt>{}{}</tt>'.format(done, missing)


def generate_html_bar(stat, bar_length):
    ratio = int(round(stat['up-to-date'] / stat['total']))
    return """
<div style="background-color:#ccc; border-radius: 5px; height:15px; width: {}px">
<div style="background-color:#337ab7; border-radius: 5px; height:15px; width: {}px"></div>
</div>""".format(5*bar_length, int(round(5*bar_length*ratio)))


class Report(DoitCmdBase):
    name = "report"
    doc_purpose = "Reports the status of tasks and subtasks"
    doc_usage = ""
    cmd_options = (opt_html, opt_bar_length)
    doc_description = """
"""

    def _execute(self, html=None, bar_length=20, pos_args=None):
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

        if html:
            progress = [generate_html_bar(stat[name], bar_length)
                        for name in cols[0]]
        else:
            progress = [generate_ascii_bar(stat[name], bar_length)
                        for name in cols[0]]

        cols.append(progress)
        cols.append([tasks[name].doc for name in cols[0]])
        t = Table(cols, names=['name'] + states + ['progress', 'doc'])

        if html:
            from astropy.table.jsviewer import DEFAULT_CSS, conf
            htmldict = {
                'table_id': 'progress',
                'table_class': 'dataTable display compact',
                'css': DEFAULT_CSS,
                'cssfiles': conf.css_urls,
                # Small hackish script to unescape the table's content ...
                'js': """
document.onreadystatechange = function () {
    if (document.readyState == 'complete') {
        Array.prototype.forEach.call(
            document.querySelectorAll('#progress td:nth-child(6)'),
            function(el) {
                el.innerHTML = el.textContent;
            }
        );
    }
}
"""
            }

            t.write(html, format='html', htmldict=htmldict)
        else:
            print(t)
            # self.outstream.write(str(t).decode('utf8') + '\n')

        self.dep_manager.close()
