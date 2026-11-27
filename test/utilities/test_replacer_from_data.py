"""The message replacer drops a line whose variables are all empty.

Run:
    .venv/bin/python manage.py test test.utilities --noinput
"""
from django.test import SimpleTestCase

from utilities.replacer_from_data import replace_parameter


class EmptyLineTestCase(SimpleTestCase):
    def test_line_with_only_empty_variables_is_dropped(self):
        body = (
            "Esto es lo que tengo.\n"
            "📅 El trabajo empezó el {{fecha}}\n"
            "💵 ${{monto}} {{frase}}\n"
            "\n"
            "Revísalo bien.")
        data = {"fecha": "", "monto": "2,500"}
        self.assertEqual(
            replace_parameter(data, body),
            "Esto es lo que tengo.\n"
            "💵 $2,500 \n"
            "\n"
            "Revísalo bien.")
