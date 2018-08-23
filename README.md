# PA core [![Build Status](https://travis-ci.com/aragaer/pa-core.svg?branch=master)](https://travis-ci.org/aragaer/pa-core) [![codecov](https://codecov.io/gh/aragaer/pa-core/branch/master/graph/badge.svg)](https://codecov.io/gh/aragaer/pa-core) [![BCH compliance](https://bettercodehub.com/edge/badge/aragaer/pa-core?branch=master)](https://bettercodehub.com/)

Main repository for simple virtual personal assistant.

`main.py` allows direct access to PA using CLI. Commands are forwarded
to the `pa-brain` component which is started separately.

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
