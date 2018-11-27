import getpass
import json
import os
import re
import select
import socket
import time

from behave import *
from nose.tools import eq_, ok_
from channels.channel import SocketChannel

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
                    if context.replies.startswith('\n'):
                        context.replies = context.replies[1:]
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
    if 'fake' in context.tags:
        while context.b._client is None:
            context.b.work(1)
    else:
        # Give real brain some time to start
        time.sleep(2)


@then('the active user is {user}')
def step_impl(context, user):
    context.b.work(1)
    msg = context.b.messages.pop(0)
    eq_(msg['command'], 'switch-user')
    eq_(msg['user'], user)


@when(u'user1 types "{text}"')
@when(u'I type "{text}"')
def step_impl(context, text):
    context.channel.write(text.encode())


@when(u'presses enter')
@when(u'press enter')
def step_impl(context):
    context.channel.write(b'\n')
    if 'fake' in context.tags:
        context.b.work(1)


@then(u'user1 sees "{text}"')
@then(u'I see "{text}"')
def step_impl(context, text):
    ok_(_expect_reply(context, text))


@given(u'the service is started')
def step_impl(context):
    context.add_cleanup(_terminate, context, "server")
    if 'fake' in context.tags:
        context.runner.start("server", with_args=['--config',
                                                  os.path.join(context.dir,
                                                               "config.yml")])
    else:
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
    if 'fake' in context.tags:
        context.b.work(1)


@given('I connected to the service')
def step_impl(context):
    context.execute_steps('''
     When I connect to the service
     Then I see "Please enter your name> "
     When I type "aragaer"
      And press enter
    ''')

@when(u'I connect to the service')
def step_impl(context):
    print("Connecting to", context.host, context.port)
    sock = socket.create_connection((context.host, context.port))
    context.channel = SocketChannel(sock)
    context.replies = ""
    context.p.register(sock.fileno(), select.POLLIN)


@then('brain sees new local channel')
def step_impl(context):
    user = getpass.getuser()
    context.execute_steps('Then the active user is {}'.format(user))
    context.b.work(1)
    msg = context.b.messages.pop(0)
    eq_(msg, {'event': 'presence',
              'from': {'user': user,
                       'channel': 'local:'+socket.gethostname()},
              'to': {"user": "niege",
                     "channel": "brain"}})


@when('brain sends "{message}" message to me')
def step_impl(context, message):
    context.b.send_message_to(message, getpass.getuser(),
                              'local:'+socket.gethostname())


@when('brain sends "{message}" message to {user}')
def step_impl(context, message, user):
    context.b.send_message_to(message, user,
                              context.channels[user])


@then('brain sees new remote channel for {user}')
def step_impl(context, user):
    context.execute_steps('Then the active user is {}'.format(user))
    context.b.work(1)
    msg = context.b.messages.pop(0)
    channel_name = msg['from']['channel']
    del msg['from']['channel']
    eq_(msg, {'event': 'presence',
              'from': {'user': user},
              'to': 'brain'})
    eq_(channel_name[:4], "tcp:")
    context.channels[user] = channel_name


@given('{user} connected to the service')
def step_impl(context, user):
    context.execute_steps("""
     When I connect to the service
     Then I see "Please enter your name> "
     When I type "{user}"
      And press enter
     Then brain sees new remote channel for {user}
""".format(user=user))


@given(u'a socket is created')
def step_impl(context):
    context.router_sock = socket.socket(socket.AF_UNIX)
    context.router_sock.bind(os.path.join(context.dir, "ROUTER"))
    context.router_sock.listen()


@given(u'the local application is connected')
def step_impl(context):
    context.execute_steps('''
        When the local application connects to it
        Then it sends the correct channel name
    ''')


@when(u'the local application connects to it')
def step_impl(context):
    context.runner.start("local", with_args=['--socket',
                                             os.path.join(context.dir,
                                                          "ROUTER")])
    context.add_cleanup(_terminate, context, "local")
    context.channel = context.runner.get_channel("local")
    context.replies = ""
    context.p.register(context.channel.get_fd(), select.POLLIN)
    print("Register fd", context.channel.get_fd())

    with timeout(0.2):
        context.endpoint_sock, _ = context.router_sock.accept()


@then(u'it sends the correct channel name')
def step_impl(context):
    expected = 'local'
    data = context.endpoint_sock.recv(1024).decode()
    lines = data.strip().split('\n')
    eq_(lines[0], expected)


@then(u'the socket receives the "{message}" message')
def step_impl(context, message):
    channel = 'local:'+socket.gethostname()
    user = getpass.getuser()
    line = context.endpoint_sock.recv(1024)
    line.endswith(b'\n')
    msg = json.loads(line.decode().strip())
    eq_(msg, {'message': message,
              'from': {'user': user,
                       'channel': channel},
              'to': {'user': 'niege',
                     'channel': 'brain'}})


@when(u'"{message}" message is sent to socket')
def step_impl(context, message):
    channel = 'local:'+socket.gethostname()
    user = getpass.getuser()
    msg = {'message': message,
           'to': {'user': user,
                  'channel': channel},
           'from': {'user': 'niege',
                    'channel': 'brain'}}
    context.endpoint_sock.send(json.dumps(msg).encode())
    context.endpoint_sock.send(b'\n')
