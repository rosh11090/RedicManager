from datetime import datetime
from django.db import models
from django.core.exceptions import ValidationError


class GlobalDictionary(models.Model):

    name = models.CharField(max_length=100, unique=True)

    def __unicode__(self):
        num_entries = self.key_value_pairs.count()
        return self.name + ': ' + unicode(num_entries) + ' entries'

    def __getitem__(self, key):
        """
        Returns the value of the selected key.
        """
        try:
            return self.key_value_pairs.get(key=key).get_value()
        except KeyValuePair.DoesNotExist:
            raise KeyError

    def __setitem__(self, key, value):
        """Sets the value of the given key in the Dictionary.

        """
        try:
            kvp = self.key_value_pairs.get(key=key)
        except KeyValuePair.DoesNotExist:
            kvp = KeyValuePair.objects.create(dictionary=self, key=key)
            kvp.set_value(value)
        else:
            kvp.set_value(value)

    def __delitem__(self, key):
        """Removed the given key from the Dictionary.

        """
        try:
            kvp = self.key_value_pairs.get(key=key)

        except KeyValuePair.DoesNotExist:
            raise KeyError

        else:
            kvp.delete()

    def __len__(self):
        """Returns the length of this Dictionary.

        """
        return self.key_value_pairs.count()

    def iterkeys(self):
        """Returns an iterator for the keys of this Dictionary.

        """
        return iter(kvp.key for kvp in self.key_value_pairs.all())

    def keys(self):
        """Returns a list of keys of this Dictionary.

        """
        return [kvp.key for kvp in self.key_value_pairs.all()]

    def itervalues(self):
        """Returns an iterator for the keys of this Dictionary.

        """
        return iter(kvp.get_value() for kvp in self.key_value_pairs.all())

    __iter__ = iterkeys

    def iteritems(self):
        """Returns an iterator over the tuples of this Dictionary.

        """
        return iter((kvp.key, kvp.get_value()) for kvp in self.key_value_pairs.all())

    def get(self, key, default=None):
        """Gets the given key from the Dictionary. If the key does not exist, it
        returns default.

        """
        try:
            return self[key]

        except KeyError:
            return default

    def has_key(self, key):
        """Returns true if the Dictionary has the given key, false if not.

        """
        return self.contains(key)

    def contains(self, key):
        """Returns true if the Dictionary has the given key, false if not.

        """
        try:
            self.key_value_pairs.get(key=key)
            return True

        except KeyValuePair.DoesNotExist:
            return False

    def clear(self):
        """Deletes all keys in the Dictionary.
        """
        self.key_value_pairs.all().delete()

    def asPyDict(self):
        """
        Get a python dictionary that represents this Dictionary object.
        This object is read-only.

        """
        fieldDict = dict()

        for kvp in self.key_value_pairs.all():
            fieldDict[kvp.key] = kvp.get_value()

        return fieldDict


class KeyValuePair(models.Model):
    VALUE_TYPE = (
        #possible types of values
        ('S', 'String'),
        ('J', 'JSON'),
        ('B', 'Boolean'),
        ('I', 'Integer'),
        ('F', 'Float'),
        ('D', 'Date'),  #format - dd/mm/yyyy
        ('T', 'Timestamp'), #format - yyyy/mm/dd/hh/mm/ss
    )
    dictionary = models.ForeignKey(GlobalDictionary, db_index=True, related_name='key_value_pairs') #n-1 relation : many KeyValuePairs correspond to same Dictionary
    key = models.CharField(max_length=100, db_index=True)
    #the value could be either of type char, int, timestamp etc
    value_type = models.CharField(max_length=2, choices=VALUE_TYPE, default='S')
    value = models.TextField(default='', blank=True) #interpret value according to value_type

    def clean(self):
        if not self.value:
            raise ValidationError('Value cannot be empty')
        if self.value_type not in zip(*self.VALUE_TYPE)[0]:
            raise ValidationError('Value type is invalid')
        if self.value_type == 'B':
            if self.value.lower() not in ['true', 'false']:
                raise ValidationError('Invalid value for boolean')
        if self.value_type == 'I':
            try:
                garbage = int(self.value)
            except:
                raise ValidationError('Invalid value for int')
        if self.value_type == 'F':
            try:
                garbage = float(self.value)
            except:
                raise ValidationError('Invalid value for float')

    def save(self, *args, **kwargs):
        self.clean()
        super(KeyValuePair, self).save(*args, **kwargs)

    def __unicode__(self):
        str = '<' + self.key + ', ' + self.value + ' ('\
              + self.get_value_type_display() + ') >'
        return str

    def get_value(self):
        if self.value_type == 'S':
            return self.value
        elif self.value_type == 'B':
            return True if self.value.lower() == 'true' else False
        elif self.value_type == 'I':
            return int(self.value)
        elif self.value_type == 'F':
            return float(self.value)
        elif self.value_type == 'D':
            list = self.value.split('/')
            d = int(list[0])
            m = int(list[1])
            y = int(list[2])
            date = datetime(y, m, d)
            return date
        elif self.value_type == 'T':
            list = self.value.split('/')
            y = int(list[0])
            mo = int(list[1])
            d = int(list[2])
            h = int(list[3])
            min = int(list[4])
            s = int(list[5])
            timestamp = datetime(y, mo, d, h, min, s)
            return timestamp
        elif self.value_type == 'GD':
            return self.value_if_dictionary
        elif self.value_type == 'DI':
            pass

    def guess_type(self, value):
        type_of_value = type(value)
        if type_of_value is int:
            self.value_type = 'I'
        elif type_of_value is str:
            self.value_type = 'S'
        elif type_of_value is bool:
            self.value_type = 'B'
        elif type_of_value is float:
            self.value_type = 'F'
        elif type_of_value is datetime.date:
            self.value_type = 'D'
        elif type_of_value is datetime.datetime:
            self.value_type = 'T'
        elif type_of_value is GlobalDictionary:
            self.value_type = 'GD'
        else:
            return False
        self.save()
        return True

    def set_value(self, value_to_set):
        #assume value_to_set is in accordance with value_type
        if type(value_to_set) is not str:
            self.guess_type(value_to_set)
        type_of_value = self.value_type
        if type_of_value == 'S':
            self.value = value_to_set
        elif type_of_value in ['I', 'F']:
            self.value = str(value_to_set)
        elif type_of_value == 'B':
            self.value = 'true' if value_to_set else 'false'
        elif type_of_value == 'D':
            val_str = str(value_to_set.day) + '/' + str(value_to_set.month) + '/' + str(value_to_set.year)
            self.value = val_str
        elif type_of_value == 'T':
            val_str = str(value_to_set.year) + '/' + str(value_to_set.month) + '/' + str(value_to_set.day) + '/'
            val_str += str(value_to_set.hour) + '/' + str(value_to_set.minute) + '/' + str(value_to_set.second)
            self.value = val_str

        self.save()