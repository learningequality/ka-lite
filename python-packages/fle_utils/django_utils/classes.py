from annoying.functions import get_object_or_None

from django.db import models
from django.contrib.messages.storage.session import SessionStorage


class NoDuplicateMessagesSessionStorage(SessionStorage):
    """
    This storage class prevents any messages from being added to the message buffer
    more than once.

    We extend the session store for AJAX-based messaging to work in Django 1.4,
       due to this bug: https://code.djangoproject.com/ticket/19387
    """

    def add(self, level, message, extra_tags=''):
        for m in self._queued_messages + self._loaded_messages:
            if m.level == level and m.message == message and m.extra_tags == extra_tags:
                return
        super(NoDuplicateMessagesSessionStorage, self).add(level, message, extra_tags)


class ExtendedModel(models.Model):
    """
    A helper class that extends the base model class,
    so we can do fun Django-y stuff that Django didn't bother to do!
    """
    class Meta:
        abstract = True

    def get_dependencies(self, passable_classes=[]):
        """
        Return list of which class names have objects
        referencing this one.

        passable_classes means classes to ignore.
        """
        class_names = []
        for related_object in (self._meta.get_all_related_objects() + self._meta.get_all_related_many_to_many_objects()):
            manager = getattr(self, related_object.get_accessor_name())
            model = getattr(manager, "model")
            if manager.all():
                class_names.append(model.__name__)
        return set(class_names) - set(passable_classes)

    def has_dependencies(self, passable_classes=[]):
        """
        Returns whether this object is referenced by any objects
        of class outside of passable_classes
        """
        return bool(self.get_dependencies(passable_classes))

    @classmethod
    def get_or_initialize(cls, **kwargs):
        """
        This is like Django's get_or_create method, but without calling save().
        Allows for more efficient post-initialize updates.

        Like get_or_Create, returns a tuple of the object, and whether it was created (True) or retrieved (False)
        """
        obj = get_object_or_None(cls, **kwargs)
        return (obj or cls(**kwargs), not bool(obj))


    def reload(self):
        '''reload the model from the database'''
        new_self = self.__class__.objects.get(pk=self.pk)
        self.__dict__.update(new_self.__dict__)
        return self
