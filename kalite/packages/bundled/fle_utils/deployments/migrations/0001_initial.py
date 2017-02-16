# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Deployment'
        db.create_table('deployments_deployment', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=250)),
            ('latitude', self.gf('django.db.models.fields.DecimalField')(max_digits=5, decimal_places=3)),
            ('longitude', self.gf('django.db.models.fields.DecimalField')(max_digits=6, decimal_places=3)),
            ('user_story', self.gf('markupfield.fields.MarkupField')(rendered_field=True)),
            ('user_story_markup_type', self.gf('django.db.models.fields.CharField')(default=None, max_length=30)),
            ('_user_story_rendered', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('deployments', ['Deployment'])


    def backwards(self, orm):
        # Deleting model 'Deployment'
        db.delete_table('deployments_deployment')


    models = {
        'deployments.deployment': {
            'Meta': {'object_name': 'Deployment'},
            '_user_story_rendered': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'latitude': ('django.db.models.fields.DecimalField', [], {'max_digits': '5', 'decimal_places': '3'}),
            'longitude': ('django.db.models.fields.DecimalField', [], {'max_digits': '6', 'decimal_places': '3'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'user_story': ('markupfield.fields.MarkupField', [], {'rendered_field': 'True'}),
            'user_story_markup_type': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '30'})
        }
    }

    complete_apps = ['deployments']