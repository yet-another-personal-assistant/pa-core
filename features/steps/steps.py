import getpass
import os
import re
import select
import socket
import time

from behave import *
from nose.tools import eq_, ok_
from runner.channel import SocketChannel

from utils import timeout


def _terminate(context, alias):
    print("Doing terminate", alias)
    try:
        context.runner.terminate(alias)
    except KeyError:
        print("{} was not started".format(alias))


def _expect_reply(context, text, seconds=None):
    if seconds is None:
        if "slow" in context.tags:
            seconds = 5
        else:
            seconds = 1

    while True:
        results = context.p.poll(seconds * 1000)
        if not results:
            print("Waited for [{}], got only [{}]".format(text, context.replies))
            return False
        for fd, event in results:
            print("Event", event, "on fd", fd)
            if fd == context.channel.get_fd():
                while True:
                    data = context.channel.read()
                    if not data:
                        break
                    context.replies += data.decode()
                if context.replies.startswith(text):
                    context.replies = context.replies[len(text):]
                    return True


@given(u'I started the main script')
@when(u'I start the main script')
def step_impl(context):
    context.add_cleanup(_terminate, context, "main")
    if 'fake' in context.tags:
        context.runner.start("main", with_args=['--config',
                                                os.path.join(context.dir,
                                                             "config.yml")])
    else:
        context.runner.start("main")
    context.channel = context.runner.get_channel("main")
    context.replies = ""
    context.p.register(context.channel.get_fd(), select.POLLIN)
    print("Register fd", context.channel.get_fd())
    time.sleep(2)
    if 'fake' in context.tags:
        context.b.work(1)


@when(u'I type "{text}"')
def step_impl(context, text):
    context.channel.write(text.encode())


@when(u'press enter')
def step_impl(context):
    context.channel.write(b'\n')
    if 'fake' in context.tags:
        context.b.work(1)


@then(u'I see "{text}"')
def step_impl(context, text):
    ok_(_expect_reply(context, text+"\n"))


@given(u'the service is started')
def step_impl(context):
    context.add_cleanup(_terminate, context, "server")
    context.runner.start("server")
    stdio = context.runner.get_channel("server")
    context.p.register(stdio.get_fd(), select.POLLIN)
    result = context.p.poll(5000)
    eq_(len(result), 1)
    fd, evt = result[0]
    eq_(fd, stdio.get_fd())
    eq_(evt, select.POLLIN)
    context.p.unregister(fd)
    line = stdio.read()
    match = re.match(r'^Server started on ([0-9\.]+):([0-9]+)$',
                     line.decode())
    ok_(match)
    context.host = match.group(1)
    context.port = int(match.group(2))


@given('I connected to the service')
@when(u'I connect to the service')
def step_impl(context):
    print("Connecting to", context.host, context.port)
    sock = socket.create_connection((context.host, context.port))
    context.channel = SocketChannel(sock)
    context.replies = ""
    context.p.register(sock.fileno(), select.POLLIN)


@then('brain sees new local channel')
def step_impl(context):
    context.b.work(1)
    msg = context.b.messages.pop(0)
    eq_(msg, {'event': 'presence',
              'from': {'user': getpass.getuser(),
                       'channel': 'local:'+socket.gethostname()},
              'to': 'brain'})


@when('brain sends "{message}" message to me')
def step_impl(context, message):
    context.b.send_message_to(message, '', '')
