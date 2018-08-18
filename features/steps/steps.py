import logging
import signal

from behave import *
from nose.tools import eq_, ok_

_LOGGER = logging.getLogger(__name__)


def _terminate(context, alias):
    try:
        context.runner.terminate(alias)
    except KeyError:
        pass


def _timeout(signum, flame):
    raise Exception("timeout")


def _expect_reply(context, text):
    signal.signal(signal.SIGALRM, _timeout)
    signal.alarm(1)
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
    signal.alarm(0)
    _LOGGER.info("Waited for [%s], got only [%s]", text, context.replies)
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
