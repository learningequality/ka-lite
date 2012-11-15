# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Settings'
        db.create_table('config_settings', (
            ('name', self.gf('django.db.models.fields.CharField')(max_length=30, primary_key=True)),
            ('value', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('datatype', self.gf('django.db.models.fields.CharField')(default='str', max_length=10)),
        ))
        db.send_create_signal('config', ['Settings'])


    def backwards(self, orm):
        
        # Deleting model 'Settings'
        db.delete_table('config_settings')


    models = {
        'config.settings': {
            'Meta': {'object_name': 'Settings'},
            'datatype': ('django.db.models.fields.CharField', [], {'default': "'str'", 'max_length': '10'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'primary_key': 'True'}),
            'value': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        }
    }

    complete_apps = ['config']
