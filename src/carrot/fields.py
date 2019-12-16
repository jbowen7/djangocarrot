from django.db import models
from django.core.exceptions import ValidationError

import json


class ListField(models.TextField):
	"""
	ListField is a textfield that serializes/unserializes Lists
	It saves lists as JSON strings.
	"""
	def from_db_value(self, value, expression, connection):
		if not value:
			return list()
		return json.loads(value)

	def get_db_prep_save(self, value, *args, **kwargs):
		if not value:
			return None
		elif not isinstance(value, list):
			raise ValidationError("Invalid input for ListField: must be a list but got: %s" % type(value))

		value = json.dumps(value)
		return super().get_db_prep_save(value, *args, **kwargs)


class DictField(models.TextField):
	"""
	DictField is a textfield that serializes/unserializes Dict
	It saves lists as JSON strings.
	"""
	def from_db_value(self, value, expression, connection):
		if not value:
			return dict()
		return json.loads(value)

	def get_db_prep_save(self, value, *args, **kwargs):
		if not value:
			return None
		elif not isinstance(value, dict):
			raise ValidationError("Invalid input for DictField: must be a list but got: %s" % type(value))

		value = json.dumps(value)
		return super().get_db_prep_save(value, *args, **kwargs)
