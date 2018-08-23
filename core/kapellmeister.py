from runner import Runner


class Kapellmeister:

    def __init__(self, config):
        self._config = config
        self._runner = Runner()

    def run(self):
        self._runner.update_config(self._config.components)
        for component in self._config.components:
            self._runner.ensure_running(component)

    def connect(self, component):
        return self._runner.get_channel(component)
