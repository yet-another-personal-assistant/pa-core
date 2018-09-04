import re
import signal
import socket

from behave import *
from nose.tools import eq_, ok_
from runner.channel import SocketChannel

from utils import timeout


def _terminate(context, alias):
    try:
        context.runner.terminate(alias)
    except KeyError:
        print("{} was not started".format(alias))


def _expect_reply(context, text):
    with timeout(1):
        while True:
            if context.replies.startswith(text):
                context.replies = context.replies[len(text):]
                return True
            try:
                message = context.channel.read()
            except:
                break
            if message:
                context.replies += message.decode()
    print("Waited for [{}], got only [{}]".format(text, context.replies))
    return False


@when(u'I start the main script')
def step_impl(context):
    context.add_cleanup(_terminate, context, "main")
    context.runner.start("main")
    context.channel = context.runner.get_channel("main")
    context.replies = ""


@then(u'I see the input prompt')
def step_impl(context):
    ok_(_expect_reply(context, "> "))


@given(u'I started the main script')
def step_impl(context):
    context.execute_steps('''
        When I start the main script
        Then I see the input prompt
    ''')


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
def step_impl(context):
    context.execute_steps('''
        When I connect to the service
        Then I see the input prompt
    ''')


@when(u'I connect to the service')
def step_impl(context):
    print("Connecting to", context.host, context.port)
    sock = socket.create_connection((context.host, context.port))
    context.channel = SocketChannel(sock)
    context.replies = ""
