# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'UpdateProgressLog.stage_status'
        db.add_column('updates_updateprogresslog', 'stage_status',
                      self.gf('django.db.models.fields.CharField')(max_length=16, null=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'UpdateProgressLog.stage_status'
        db.delete_column('updates_updateprogresslog', 'stage_status')


    models = {
        'updates.updateprogresslog': {
            'Meta': {'object_name': 'UpdateProgressLog'},
            'cancel_requested': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'completed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'current_stage': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'end_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'process_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'process_percent': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'stage_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'}),
            'stage_percent': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'stage_status': ('django.db.models.fields.CharField', [], {'max_length': '16', 'null': 'True'}),
            'start_time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'total_stages': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'updates.videofile': {
            'Meta': {'ordering': "['priority', 'youtube_id']", 'object_name': 'VideoFile'},
            'cancel_download': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'download_in_progress': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'flagged_for_download': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'percent_complete': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'priority': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'youtube_id': ('django.db.models.fields.CharField', [], {'max_length': '20', 'primary_key': 'True'})
        }
    }

    complete_apps = ['updates']