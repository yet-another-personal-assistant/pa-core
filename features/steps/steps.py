import json
import os
import re
import select
import socket
import threading
import time

from behave import *
from nose.tools import eq_, ok_
from runner.channel import SocketChannel

from utils import timeout


class UserSession:

    def __init__(self, name, channel):
        self.name = name
        self.channel = channel
        self.replies = ""


def _terminate(context, alias):
    print("Doing terminate", alias)
    try:
        context.runner.terminate(alias)
    except KeyError:
        print("{} was not started".format(alias))


def _send_delayed(channel, data, delay):
    time.sleep(delay)
    channel.write(data)


def _fake_brain_response(context, line):
    msg = json.loads(line)
    text = msg['message']
    reply = context.fixed_replies.get(text, text)
    if reply is not None:
        message = json.dumps({'message': reply,
                              'from': msg['to'],
                              'to': msg['from']}).encode()+b'\n'
        delay = context.reply_delays.get(text, 0)
        if delay:
            th = threading.Thread(target=_send_delayed,
                                  args=(context.brain, message, delay))
            context.add_cleanup(th.join)
            th.start()
        else:
            context.brain.write(message)


def _user_by_name(context, user):
    for session in context.users.values():
        if session.name == user:
            return session
    else:
        print("User", user, "is not registered")


def _expect_reply(context, user, text, seconds=None):
    if seconds is None:
        if "slow" in context.tags:
            seconds = 5
        else:
            seconds = 1

    this_user = _user_by_name(context, user)
    ok_(this_user)

    while True:
        if this_user.replies.startswith(text):
            this_user.replies = this_user.replies[len(text):]
            return True
        results = context.poller.poll(seconds)
        if not results:
            print("Waited for [{}], got only [{}]".format(text,
                                                          this_user.replies))
            return False
        for line, channel in results:
            if channel in context.users:
                session = context.users[channel]
                session.replies += line.decode()
            elif channel == context.brain:
                _fake_brain_response(context, line)


@given(u'I started the main script')
@when(u'I start the main script')
def step_impl(context):
    args = []
    if 'fake' in context.tags:
        start_fake_brain(context)
        args += ["--config", context.config_file]
    context.add_cleanup(_terminate, context, "main")
    context.runner.start("main", with_args=args)
    chan = context.runner.get_channel("main")
    context.users[chan] = UserSession("I", chan)
    context.poller.register(chan)
    if 'fake' in context.tags:
        accept_fake_brain(context)


@when(u'{user} types "{text}"')
@when(u'{user} type "{text}"')
def step_impl(context, user, text):
    _user_by_name(context, user).channel.write(text.encode())
    context.last_user = user


@when(u'press enter')
@when(u'presses enter')
def step_impl(context):
    _user_by_name(context, context.last_user).channel.write(b'\n')


@when('{user} sends "{text}"')
def step_impl(context, user, text):
    _user_by_name(context, user).channel.write(text.encode(), b'\n')


@then('{user} see "{text}"')
@then('{user} sees "{text}"')
def step_impl(context, user, text):
    ok_(_expect_reply(context, user, text+"\n"))


@then('{user} see nothing')
@then('{user} sees nothing')
def step_impl(context, user):
    _expect_reply(context, user, "any text\n")
    eq_(_user_by_name(context, user).replies, "")


@given(u'the service is started')
def step_impl(context):
    args = []
    if 'fake' in context.tags:
        start_fake_brain(context)
        args += ["--config", context.config_file]
    context.add_cleanup(_terminate, context, "server")
    context.runner.start("server", with_args=args)
    connect_to_server(context)
    if 'fake' in context.tags:
        accept_fake_brain(context)


def start_fake_brain(context):
    context.socket = socket.socket()
    context.socket.bind(('127.0.0.1', 0))
    context.socket.listen()
    context.host, context.port = context.socket.getsockname()
    context.add_cleanup(context.socket.close)
    context.config_file = os.path.join(context.dir, "config.yml")
    with open(context.config_file, "w") as config:
        config.write("""components:
  brain:
    command: nc {} {}
    buffering: line""".format(context.host, context.port))


def accept_fake_brain(context):
    sock, _ = context.socket.accept()
    context.brain = SocketChannel(sock)
    context.add_cleanup(context.brain.close)
    context.poller.register(context.brain)


def connect_to_server(context):
    stdio = context.runner.get_channel("server")
    context.poller.register(stdio)
    result = context.poller.poll(5)
    eq_(len(result), 1)
    line, chan = result[0]
    eq_(chan, stdio)
    context.poller.unregister(stdio)
    match = re.match(r'^Server started on ([0-9\.]+):([0-9]+)$',
                     line.decode())
    ok_(match)
    context.host = match.group(1)
    context.port = int(match.group(2))


@when('{user} is connected to the service')
def step_impl(context, user):
    sock = socket.create_connection((context.host, context.port))
    chan = SocketChannel(sock)
    context.users[chan] = UserSession(user, chan)
    context.poller.register(chan)


@given('I connected to the service')
@when(u'I connect to the service')
def step_impl(context):
    context.execute_steps("When I is connected to the service")


@given('that brain should reply')
def step_impl(context):
    for row in context.table.rows:
        phrase, response = row[0], row[1]
        delay = float(row[2]) if len(row) > 2 else 0
        if response == 'None':
            response = None
        context.fixed_replies[phrase] = response
        context.reply_delays[phrase] = delay
