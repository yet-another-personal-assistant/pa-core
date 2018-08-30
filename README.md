# PA core [![Build Status](https://travis-ci.com/aragaer/pa-core.svg?branch=master)](https://travis-ci.org/aragaer/pa-core) [![codecov](https://codecov.io/gh/aragaer/pa-core/branch/master/graph/badge.svg)](https://codecov.io/gh/aragaer/pa-core) [![BCH compliance](https://bettercodehub.com/edge/badge/aragaer/pa-core?branch=master)](https://bettercodehub.com/)

Main repository for simple virtual personal assistant.

`main.py` allows direct access to PA using CLI. Commands are forwarded
to the `pa-brain` component which is started separately.

## Configuration

Configuration is defined in `config.yml` file. Example of `config.yml`:

    variables:
      translator_socket: tmpfile
    components:
      translator:
        cwd: pa2human
        command: ./pa2human.py --socket ${translator_socket}
        type: socket
        socket: ${translator_socket}
      brain:
        cwd: brain
        command: sbcl --script run.lisp --translator ${translator_socket}
        buffering: line
        after: translator

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

## Requirements

### Brain
- `pa-brain` component must be located in the brain
  directory. Currently hardcoded as a Common Lisp application started
  with `sbcl --script run.lisp` command. Currently retrieved as a git
  submodule from [pa_brain repository](https://github.com/aragaer/pa_brain).

## Protocol

Messages sent between `main.py` and `pa-brain` are one-lined json
objects having the following fields:

- `message`: text sent by user or pa
- `from`: anything
- `to`: anything

`from` and `to` fields are not currently used but are required by the
current `pa-brain` implementation.
