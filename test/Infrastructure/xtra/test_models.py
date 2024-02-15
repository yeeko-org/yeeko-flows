from django.test import TestCase
from infrastructure.xtra.models import (
    ClassifyExtra, Format, Extra, PresetValue
)
from infrastructure.xtra.factories import (
    ClassifyExtraFactory, FormatFactory, ExtraFactory, PresetValueFactory
)


class ClassifyExtraTestCase(TestCase):
    def test_create_classify_extra(self):
        classify_extra = ClassifyExtraFactory()
        self.assertIsInstance(classify_extra, ClassifyExtra)


class FormatTestCase(TestCase):
    def test_create_format(self):
        format_instance = FormatFactory()
        self.assertIsInstance(format_instance, Format)


class ExtraTestCase(TestCase):
    def test_create_extra(self):
        extra_instance = ExtraFactory()
        self.assertIsInstance(extra_instance, Extra)


class PresetValueTestCase(TestCase):
    def test_create_preset_value(self):
        preset_value = PresetValueFactory()
        self.assertIsInstance(preset_value, PresetValue)
