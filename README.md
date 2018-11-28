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

`app.py` is a main script for starting the application. It starts the
router and two endpoints -- tcp and incoming.

`main.py` and `server.py` are deprecated scripts. `main.py` is
essentially a `router.py`+`local.py` and `server.py` is
`router.py`+`tcp.py`

## Configuration

Currently two separate configuration files are used: `config.yml` and
`config_new.yml`. Example of `config.yml`:

    variables:
      translator_socket: tmpfile
    components:
      translator:
        cwd: pa2human
        command: ./pa2human.py --socket ${translator_socket}
        wait-for: ${translator_socket}
      brain:
        cwd: brain
        command: sbcl --script run.lisp --translator ${translator_socket}
        buffering: line
        after: translator

Example of `config_new.yml`:

     components:
       router:
         cwd: .
         command: ./router.py --socket router_socket
         wait-for: router_socket
       tcp:
         cwd: .
         command: ./tcp.py --socket router_socket
         after: router
       incoming:
         cwd: .
         command: ./incoming.py --socket router_socket
         after: router


`variables` section is optional. It lists variables to be substituted
in the rest of the configuration file. Currently only `tmpfile` type
is supported which is a unique filename.

`components` section describes components to be started. Component
definition uses the following fields:

- `command` _Mandatory_: The command to start the component.
- `cwd`: Working directory for the component. Default is the current directory.
- `type`: How to communicate to the component. Currently supported are `socket` (UNIX socket) and `stdio`. Default is `stdio`.
- `buffering`: If defined and set to `line`, line buffering is used for communication.
- `socket`: Mandatory for `socket` type components. Name of the socket file that is expected to be created by the component.
- `after`: Defines ordering for components. Can be either single component or a list of components.
- `wait-for`: Should be a name of a file created by the command.

## Requirements

### Translator
`pa2human` component. Currently defined in config.yml as a Python
script started with `./pa2human.py` command in `pa2human`
directory. Currently retrieved as a git submodule from [pa2human
repository](https://github.com/aragaer/pa2human). Not used directly.

### Brain
`pa-brain` component. Currently defined in config.yml as a Common Lisp
application started with `sbcl --script run.lisp` command in `brain`
directory. Currently retrieved as a git submodule from [pa_brain
repository](https://github.com/aragaer/pa_brain).

## Protocol

Messages sent between `main.py` and `pa-brain` are one-lined json
objects having the following fields:

- `message`: text sent by user or pa
- `from`: anything
- `to`: anything

`from` and `to` fields are not currently used but are required by the
current `pa-brain` implementation.
