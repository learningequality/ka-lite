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
        for m in self._queued_messages:
            if m.level == level and m.message == message and m.extra_tags == extra_tags:
                return
        super(NoDuplicateMessagesSessionStorage, self).add(level, message, extra_tags)


class ExtendedModel(models.Model):
    """
    A helper class that extends the base model class to allow extra functionality to be passed in.  
    """

    def get_dependencies(self, passable_classes=[]):
        """Return list of related objects"""
        class_names = []
        for related_object in (self._meta.get_all_related_objects() + self._meta.get_all_related_many_to_many_objects()):
            manager = getattr(self, related_object.get_accessor_name())
            model = getattr(manager, "model")
            if manager.all():
                class_names.append(model.__name__)
        print class_names
        return set(class_names) - set(passable_classes)

    def has_dependencies(self, passable_classes=[]):
        return bool(self.get_dependencies(passable_classes))

    class Meta:
        abstract = True