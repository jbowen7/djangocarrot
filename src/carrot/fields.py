from django.db import models
from django.core.exceptions import ValidationError

import json


class ListField(models.TextField):
	"""
	ListField is a textfield that serializes/unserializes Lists
	It saves lists as JSON strings.
	"""
	def from_db_value(self, value, expression, connection):
		value = "[" + value + "]"
		return json.loads(value)

	def get_db_prep_save(self, value, *args, **kwargs):
		if value in ['', None]:
			value = []
		elif not isinstance(value, list):
			raise ValidationError("Invalid input for ListField: must be a list but got: %s" % type(value))

		value = json.dumps(value)
		value = value.lstrip('[').rstrip(']')
		return super().get_db_prep_save(value, *args, **kwargs)


class DictField(models.TextField):
	"""
	DictField is a textfield that serializes/unserializes Dict
	It saves lists as JSON strings.
	"""
	def from_db_value(self, value, expression, connection):
		value = "{" + value + "}"
		return json.loads(value)

	def get_db_prep_save(self, value, *args, **kwargs):
		if value in ['', None]:
			value = {}
		elif not isinstance(value, dict):
			raise ValidationError("Invalid input for DictField: must be a list but got: %s" % type(value))

		value = json.dumps(value)
		value = value.lstrip('{').rstrip('}')
		return super().get_db_prep_save(value, *args, **kwargs)
