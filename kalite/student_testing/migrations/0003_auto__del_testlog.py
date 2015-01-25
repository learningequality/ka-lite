# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting model 'TestLog'
        db.delete_table(u'student_testing_testlog')


    def backwards(self, orm):
        # Adding model 'TestLog'
        db.create_table(u'student_testing_testlog', (
            ('index', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('complete', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('started', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['securesync.FacilityUser'])),
            ('test', self.gf('django.db.models.fields.CharField')(max_length=100)),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal(u'student_testing', ['TestLog'])


    models = {
        
    }

    complete_apps = ['student_testing']