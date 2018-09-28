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
        results = context.poll.poll(seconds * 1000)
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
    context.runner.start("main")
    context.channel = context.runner.get_channel("main")
    context.replies = ""
    context.poll.register(context.channel.get_fd())
    print("Register fd", context.channel.get_fd()) 
    time.sleep(2)


@when(u'I type "{text}"')
def step_impl(context, text):
    context.channel.write(text.encode())


@when(u'press enter')
def step_impl(context):
    context.channel.write(b'\n')


@then(u'I see "{text}"')
def step_impl(context, text):
    ok_(_expect_reply(context, text+"\n"))


@given(u'the service is started')
def step_impl(context):
    context.add_cleanup(_terminate, context, "server")
    context.runner.start("server")
    stdio = context.runner.get_channel("server")
    with timeout(5):
        while True:
            line = stdio.read()
            if line:
                break
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
