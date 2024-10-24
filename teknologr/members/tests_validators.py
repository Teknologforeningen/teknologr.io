from django.test import TestCase
from django.core.exceptions import ValidationError
from .validators import CommonValidators

class Validator(CommonValidators):
    cleaned_data = {}

class ValidatorTest(TestCase):
    def setUp(self):
        self.validator = Validator()

    def setData(self, prop, value):
        self.validator.cleaned_data[prop] = value

    def test_clean_given_names_ok(self):
        for name in [
            "Svakar",
            "Svakar Svante",
            "Svakar-Svante",
            " Svakar ",
            "Pär",
            "Áìñö",
        ]:
            self.setData("given_names", name)
            self.validator.clean_given_names()

    def test_clean_given_names_error(self):
        for c in "3_@<>=?!#%/\\*'\"^":
            self.setData("given_names", f"Svakar{c}")
            with self.assertRaises(ValidationError):
                self.validator.clean_given_names()

    def test_clean_surname_ok(self):
        for name in [
            "Teknolog",
            " af Teknolog ",
            "von Teknolog-Teekkari",
            "Ingenjör",
            "Áìñö",
        ]:
            self.setData("surname", name)
            self.validator.clean_surname()

    def test_clean_surname_error(self):
        for c in "3_@<>=?!#%/\\*'\"^":
            self.setData("surname", f"Teknolog{c}")
            with self.assertRaises(ValidationError):
                self.validator.clean_surname()

    def test_clean_phone_ok(self):
        for number in [
            "040123456",
            "040-123 234",
            "123 - 456 - 789",
            " 040123456 ",
            "+358 40 - 123",
        ]:
            self.setData("phone", number)
            self.validator.clean_phone()

    def test_clean_phone_error(self):
        for number in [
            "040123456g",
            "040123456,331",
            "+ 358123",
            "-040123456",
            "040123456-",
        ]:
            self.setData("phone", number)
            with self.assertRaises(ValidationError):
                self.validator.clean_phone()
