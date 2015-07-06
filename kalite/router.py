class TopicToolsRouter():
    """
    A router to control database operations for the following models in the topic_tools app:
    * AssessmentItem

    This is meant to be a "static" database -- used so this data exposes Django ORM methods, and can be conservatively
    loaded into memory, but not modified by an end user. The only writes should be during the installation setup.

    See: https://docs.djangoproject.com/en/1.5/topics/db/multi-db/#database-routers
    """
    MODELS = ("AssessmentItem",)

    def db_for_read(self, model, **hints):
        """
        Send requests for specific Models to the assessment_items db.
        """
        return self._the_db_or_none(model)

    def db_for_write(self, model, **hints):
        """
        Send requests for specific Models to the assessment_items db.
        """
        return self._the_db_or_none(model)

    def _the_db_or_none(self, model):
        """
        Given a model, choose the right DB depending on its name. Returning None in this case will cause it to fall back
        to the default router.
        """
        if model.__name__ in self.MODELS:
            return "assessment_items"
        else:
            return None

    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations between the given models only.
        """
        if type(obj1).__name__ in self.MODELS and type(obj2).__name__ in self.MODELS:
            return True
        return None

    def allow_syncdb(self, db, model):
        """
        Make sure the given models only appear in the assessment_items db.
        """
        if db == 'assessment_items':
            return model.__name__ in self.MODELS
        elif model.__name__ in self.MODELS:
            return False  # Don't sync these models to any other DB
        return None