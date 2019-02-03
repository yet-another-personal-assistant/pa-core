# PA core [![Build Status](https://travis-ci.com/aragaer/pa-core.svg?branch=master)](https://travis-ci.org/aragaer/pa-core) [![codecov](https://codecov.io/gh/aragaer/pa-core/branch/master/graph/badge.svg)](https://codecov.io/gh/aragaer/pa-core) [![BCH compliance](https://bettercodehub.com/edge/badge/aragaer/pa-core?branch=master)](https://bettercodehub.com/)

Main repository for simple virtual personal assistant.

`router.py` is the central component for routing messages between user
channels and brains.

`tcp.py` is an endpoint that connects to a running router and listens
for incoming TCP connections.

`local.py` is an endpoint that connects to a running router and allows
access to PA using CLI.

`incoming.py` is an endpoint that creates a named pipe that accepts
system events and forwards them to router.

## Running

In order to start the system its components have to be started in
correct order:

- pa-translator can be started independently
- pa-router can be started independently
- pa-brain depends on both pa-translator and pa-router
- pa-tcp, pa-local and pa-incoming depend on pa-router

## Requirements

### Translator
`pa-translator` component.  Currently retrieved as a git submodule
from [pa2human repository](https://github.com/aragaer/pa2human). Not
used directly.

### Brain
`pa-brain` component. Currently retrieved as a git submodule from
[pa_brain repository](https://github.com/aragaer/pa_brain).

## Protocol

Messages sent between client and `pa-brain` are one-lined json objects
having the following fields:

- `message`: text sent by user or pa
- `from`:
  - `user`: username
  - `channel`: anything
- `to`:
  - `user`: username
  - `channel`: anything

Intermediate components will modify the `channel` field as messages
passes through. Messages sent by user should have `to` equal to
`{"user": "niege", "channel": "brain"}`. Messages from `pa-brain` will
have the `from` field equal to same value.
