# PA core

Main repository for simple virtual personal assistant.

`main.py` allows direct access to PA using CLI. Commands are forwarded to the `pa-brain` component which is started separately.

## Requirements

### Brain
- `pa-brain` component must be located in the brain directory. Currently hardcoded as a Common Lisp application started with `sbcl --script run.lisp` command. Currently retrieved as a git submodule from [pa_brain repository](https://github.com/aragaer/pa_brain).

## Protocol

Messages sent between `main.py` and `pa-brain` are one-lined json objects having the following fields:

- `message`: text sent by user or pa
- `from`: anything
- `to`: anything

`from` and `to` fields are not currently used but are required by the current `pa-brain` implementation.
