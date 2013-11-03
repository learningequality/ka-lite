# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'UpdateProgressLog.total_stages'
        db.alter_column('updates_updateprogresslog', 'total_stages', self.gf('django.db.models.fields.IntegerField')(null=True))

    def backwards(self, orm):

        # Changing field 'UpdateProgressLog.total_stages'
        db.alter_column('updates_updateprogresslog', 'total_stages', self.gf('django.db.models.fields.IntegerField')())

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
            'total_stages': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['updates']