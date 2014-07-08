# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'UpdateProgressLog'
        db.create_table('updates_updateprogresslog', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('process_name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('process_percent', self.gf('django.db.models.fields.FloatField')(default=0)),
            ('stage_name', self.gf('django.db.models.fields.CharField')(max_length=100, null=True)),
            ('stage_percent', self.gf('django.db.models.fields.FloatField')(default=0)),
            ('total_stages', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('notes', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('start_time', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('end_time', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('completed', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('updates', ['UpdateProgressLog'])


    def backwards(self, orm):
        # Deleting model 'UpdateProgressLog'
        db.delete_table('updates_updateprogresslog')


    models = {
        'updates.updateprogresslog': {
            'Meta': {'object_name': 'UpdateProgressLog'},
            'completed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'end_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'process_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'process_percent': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'stage_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'}),
            'stage_percent': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'start_time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'total_stages': ('django.db.models.fields.IntegerField', [], {'default': '1'})
        }
    }

    complete_apps = ['updates']