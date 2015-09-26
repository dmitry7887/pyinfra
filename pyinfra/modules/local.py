# pyinfra
# File: pyinfra/modules/local.py
# Desc: run stuff locally, within the context of operations

from subprocess import Popen, PIPE

import gevent
from termcolor import colored

from pyinfra.api import operation
from pyinfra.api.util import read_buffer


def _run_local(code, hostname, host, print_output=False, print_prefix=None):
    '''Subprocess based implementation of pyinfra/api/ssh.py's run_shell_command.'''
    process = Popen(code, shell=True, stdout=PIPE, stderr=PIPE)

    # Note that gevent's subprocess module does not allow for "live" reading from a process,
    # so the readlines() calls below only return once the process is complete. Thus the whole
    # greenlet spawning/etc below is *currently* pointless.

    # TODO: implement fake file object as a pipe to read from/to as buffer, live
    # see: https://bitbucket.org/eriks5/gevent-subprocess/src/550405f060a5f37167c0be042baaee6075b3d28e/src/gevsubprocess/pipe.py?at=default
    stdout_reader = gevent.spawn(
        read_buffer, process.stdout.readlines(),
        print_output=print_output,
        print_func=lambda line: u'{0}{1}'.format(print_prefix, line)
    )
    stderr_reader = gevent.spawn(
        read_buffer, process.stderr.readlines(),
        print_output=print_output,
        print_func=lambda line: u'{0}{1}'.format(print_prefix, colored(line, 'red'))
    )

    # Wait for the process to complete & return
    gevent.wait((stdout_reader, stderr_reader))
    return process.wait() <= 0


@operation
def shell(*code):
    '''Runs shell commands locally in a subprocess.'''
    return [
        (lambda *args, **kwargs: _run_local(c, *args, **kwargs), (), {})
        for c in code
    ]