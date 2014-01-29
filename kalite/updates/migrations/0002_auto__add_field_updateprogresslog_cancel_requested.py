# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'UpdateProgressLog.cancel_requested'
        db.add_column('updates_updateprogresslog', 'cancel_requested',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'UpdateProgressLog.cancel_requested'
        db.delete_column('updates_updateprogresslog', 'cancel_requested')


    models = {
        'updates.updateprogresslog': {
            'Meta': {'object_name': 'UpdateProgressLog'},
            'cancel_requested': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
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