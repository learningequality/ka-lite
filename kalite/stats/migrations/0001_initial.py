# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'UnregisteredDevice'
        db.create_table('stats_unregistereddevice', (
            ('id', self.gf('django.db.models.fields.CharField')(max_length=32, primary_key=True)),
        ))
        db.send_create_signal('stats', ['UnregisteredDevice'])

        # Adding model 'UnregisteredDevicePing'
        db.create_table('stats_unregistereddeviceping', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('device', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['stats.UnregisteredDevice'], unique=True)),
            ('npings', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('last_ip', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('last_ping', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('stats', ['UnregisteredDevicePing'])


    def backwards(self, orm):
        # Deleting model 'UnregisteredDevice'
        db.delete_table('stats_unregistereddevice')

        # Deleting model 'UnregisteredDevicePing'
        db.delete_table('stats_unregistereddeviceping')


    models = {
        'stats.unregistereddevice': {
            'Meta': {'object_name': 'UnregisteredDevice'},
            'id': ('django.db.models.fields.CharField', [], {'max_length': '32', 'primary_key': 'True'})
        },
        'stats.unregistereddeviceping': {
            'Meta': {'object_name': 'UnregisteredDevicePing'},
            'device': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['stats.UnregisteredDevice']", 'unique': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_ip': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'last_ping': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'npings': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        }
    }

    complete_apps = ['stats']