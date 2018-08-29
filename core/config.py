from collections import OrderedDict
from contextlib import suppress

import networkx
import yaml

from jsonschema import validate
from jsonschema.exceptions import ValidationError


class ConfigError(ValueError):
    pass


_COMMAND_SCHEMA = {"type": "string"}

_COMPONENT_SCHEMA = {
    "type": "object",
    "required": ["command"],
    "properties": {
        "command": _COMMAND_SCHEMA}}

_CONFIG_SCHEMA = {
    "type": "object",
    "required": ["components"],
    "properties": {
        "variables": {"type": "object"},
        "components": {
            "patternProperties": {
                "": _COMPONENT_SCHEMA}}}}


def _config_error(ve):
    path = list(ve.path)
    if ve.validator == 'type' and ve.instance is not None:
        path.append(ve.instance)
    if path:
        what = "'{}'".format('/'.join(path))
    else:
        what = '<root>'
    if ve.validator == 'required':
        missing = ', '.join(ve.validator_value)
        msg = "No '{}' in {}".format(missing, what)
    elif ve.validator == 'type':
        t = {"object": "mapping"}[ve.validator_value]
        msg = "{} is not a {}".format(what, t)
    else:
        msg = ve
    raise ConfigError(msg)


def _sort(components):
    graph = networkx.DiGraph()
    for component, definition in components.items():
        graph.add_node(component)
        if 'after' in definition:
            graph.add_edge(definition['after'], component)
    with suppress(StopIteration):
        cycle = next(networkx.simple_cycles(graph))
        raise ConfigError("Dependency loop: " + ' -> '.join(cycle))
    result = OrderedDict()
    for component in networkx.topological_sort(graph):
        result[component] = components[component]
    return result


class Config:

    def __init__(self, cfg):
        self._config = yaml.load(cfg)

        try:
            validate(self._config, _CONFIG_SCHEMA)
        except ValidationError as ve:
            _config_error(ve)

        for toplevel in ('components', 'variables'):
            if self._config.get(toplevel) is None:
                self._config[toplevel] = {}

        self._config['variables'] = {
            n: {'type': t} for n, t in self._config['variables'].items()}

        self._components = _sort(self._config['components'])

    @property
    def components(self):
        return self._components

    @property
    def variables(self):
        return self._config['variables']
