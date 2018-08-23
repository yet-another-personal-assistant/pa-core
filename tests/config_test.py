import unittest

from core import Config, ConfigError


ONE_COMPONENT = """
components:
  component:
    command: command
"""


class ConfigTest(unittest.TestCase):

    def test_parse_empty_config(self):
        tests = {"": "<root> is not a mapping",
                 "hi\n": "'hi' is not a mapping",
                 "hi:\n  x\n": "No 'components' in <root>"}
        for cfg, err in tests.items():
            with self.assertRaisesRegex(ConfigError, err):
                Config(cfg)

    def test_parse_no_components(self):
        config = Config("components:\n")

        self.assertEqual(len(config.components), 0)

    def test_parse_component(self):
        config = Config(ONE_COMPONENT)

        self.assertEqual(list(config.components), ["component"])
        component = config.components["component"]
        self.assertEqual(component["command"], "command")

    def test_incorrect_component(self):
        with self.assertRaisesRegex(ConfigError,
                                    "'components/component' is not a mapping"):
            Config("components:\n  component:\n")

        with self.assertRaisesRegex(ConfigError,
                                    "No 'command' in 'components/component'"):
            Config("components:\n  component:\n    stuff: 1\n")

    def test_independent(self):
        config = Config("""
            components:
              component1:
                command: command1
              component2:
                command: command2
        """)

        self.assertEqual(set(config.components), {"component1", "component2"})

    def test_dependency(self):
        config = Config("""
            components:
              component1:
                command: command1
              component2:
                command: command2
                after: component1
        """)

        self.assertEqual(list(config.components), ["component1", "component2"])

    def test_dependency2(self):
        config = Config("""
            components:
              component1:
                command: command1
                after: component2
              component2:
                command: command2
        """)

        self.assertEqual(list(config.components), ["component2", "component1"])

    def test_dependency_cycle(self):
        cfg = """
            components:
              component1:
                command: command1
                after: component2
              component2:
                command: command2
                after: component1
        """
        err = "Dependency loop: component[12] -> component[12]"

        with self.assertRaisesRegex(ConfigError, err):
            Config(cfg)
