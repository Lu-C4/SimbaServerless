import unittest

from src.commands import commands
from src.core.command_handler import get_command
from src.core.component_handler import get_fn


class RoutingTests(unittest.TestCase):
    def test_registered_command_is_resolved_by_name(self):
        command = get_command({"data": {"name": "credits"}})
        self.assertIs(command, commands["credits"])

    def test_unknown_command_is_not_resolved(self):
        self.assertIsNone(get_command({"data": {"name": "missing"}}))

    def test_registered_component_is_resolved_by_custom_id(self):
        self.assertIsNotNone(get_fn({"data": {"custom_id": "namerecruit"}}))


if __name__ == "__main__":
    unittest.main()
