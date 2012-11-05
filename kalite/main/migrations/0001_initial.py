# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'VideoLog'
        db.create_table('main_videolog', (
            ('id', self.gf('django.db.models.fields.CharField')(max_length=32, primary_key=True)),
            ('counter', self.gf('django.db.models.fields.IntegerField')()),
            ('signature', self.gf('django.db.models.fields.CharField')(max_length=360, blank=True)),
            ('signed_version', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('signed_by', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', null=True, to=orm['securesync.Device'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['securesync.FacilityUser'], null=True, blank=True)),
            ('youtube_id', self.gf('django.db.models.fields.CharField')(max_length=11, db_index=True)),
            ('total_seconds_watched', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('points', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('complete', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('main', ['VideoLog'])

        # Adding model 'ExerciseLog'
        db.create_table('main_exerciselog', (
            ('id', self.gf('django.db.models.fields.CharField')(max_length=32, primary_key=True)),
            ('counter', self.gf('django.db.models.fields.IntegerField')()),
            ('signature', self.gf('django.db.models.fields.CharField')(max_length=360, blank=True)),
            ('signed_version', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('signed_by', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', null=True, to=orm['securesync.Device'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['securesync.FacilityUser'], null=True, blank=True)),
            ('exercise_id', self.gf('django.db.models.fields.CharField')(max_length=50, db_index=True)),
            ('streak_progress', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('attempts', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('complete', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('main', ['ExerciseLog'])


    def backwards(self, orm):
        
        # Deleting model 'VideoLog'
        db.delete_table('main_videolog')

        # Deleting model 'ExerciseLog'
        db.delete_table('main_exerciselog')


    models = {
        'main.exerciselog': {
            'Meta': {'object_name': 'ExerciseLog'},
            'attempts': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'complete': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'counter': ('django.db.models.fields.IntegerField', [], {}),
            'exercise_id': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '32', 'primary_key': 'True'}),
            'signature': ('django.db.models.fields.CharField', [], {'max_length': '360', 'blank': 'True'}),
            'signed_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['securesync.Device']"}),
            'signed_version': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'streak_progress': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['securesync.FacilityUser']", 'null': 'True', 'blank': 'True'})
        },
        'main.videolog': {
            'Meta': {'object_name': 'VideoLog'},
            'complete': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'counter': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '32', 'primary_key': 'True'}),
            'points': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'signature': ('django.db.models.fields.CharField', [], {'max_length': '360', 'blank': 'True'}),
            'signed_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['securesync.Device']"}),
            'signed_version': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'total_seconds_watched': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['securesync.FacilityUser']", 'null': 'True', 'blank': 'True'}),
            'youtube_id': ('django.db.models.fields.CharField', [], {'max_length': '11', 'db_index': 'True'})
        },
        'securesync.device': {
            'Meta': {'object_name': 'Device'},
            'counter': ('django.db.models.fields.IntegerField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '32', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'public_key': ('django.db.models.fields.CharField', [], {'max_length': '200', 'db_index': 'True'}),
            'signature': ('django.db.models.fields.CharField', [], {'max_length': '360', 'blank': 'True'}),
            'signed_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['securesync.Device']"}),
            'signed_version': ('django.db.models.fields.IntegerField', [], {'default': '1'})
        },
        'securesync.facility': {
            'Meta': {'object_name': 'Facility'},
            'address': ('django.db.models.fields.CharField', [], {'max_length': '400', 'blank': 'True'}),
            'address_normalized': ('django.db.models.fields.CharField', [], {'max_length': '400', 'blank': 'True'}),
            'counter': ('django.db.models.fields.IntegerField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '32', 'primary_key': 'True'}),
            'latitude': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'longitude': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'signature': ('django.db.models.fields.CharField', [], {'max_length': '360', 'blank': 'True'}),
            'signed_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['securesync.Device']"}),
            'signed_version': ('django.db.models.fields.IntegerField', [], {'default': '1'})
        },
        'securesync.facilityuser': {
            'Meta': {'unique_together': "(('facility', 'username'),)", 'object_name': 'FacilityUser'},
            'counter': ('django.db.models.fields.IntegerField', [], {}),
            'facility': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['securesync.Facility']"}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '32', 'primary_key': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'signature': ('django.db.models.fields.CharField', [], {'max_length': '360', 'blank': 'True'}),
            'signed_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['securesync.Device']"}),
            'signed_version': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '30'})
        }
    }

    complete_apps = ['main']
