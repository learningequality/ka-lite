# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'StoreTransactionLog'
        db.create_table(u'store_storetransactionlog', (
            ('id', self.gf('django.db.models.fields.CharField')(max_length=32, primary_key=True)),
            ('counter', self.gf('django.db.models.fields.IntegerField')(default=None, null=True, blank=True)),
            ('signature', self.gf('django.db.models.fields.CharField')(max_length=360, null=True, blank=True)),
            ('signed_version', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('signed_by', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', null=True, to=orm['securesync.Device'])),
            ('zone_fallback', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', null=True, to=orm['securesync.Zone'])),
            ('deleted', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['securesync.FacilityUser'])),
            ('value', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('context_id', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('context_type', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('reversible', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('item', self.gf('django.db.models.fields.CharField')(max_length=100, db_index=True)),
            ('purchased_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'store', ['StoreTransactionLog'])


    def backwards(self, orm):
        # Deleting model 'StoreTransactionLog'
        db.delete_table(u'store_storetransactionlog')


    models = {
        'securesync.device': {
            'Meta': {'object_name': 'Device'},
            'counter': ('django.db.models.fields.IntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '32', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'public_key': ('django.db.models.fields.CharField', [], {'max_length': '500', 'db_index': 'True'}),
            'signature': ('django.db.models.fields.CharField', [], {'max_length': '360', 'null': 'True', 'blank': 'True'}),
            'signed_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['securesync.Device']"}),
            'signed_version': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'version': ('django.db.models.fields.CharField', [], {'default': "'0.9.2'", 'max_length': '9', 'blank': 'True'}),
            'zone_fallback': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['securesync.Zone']"})
        },
        'securesync.facility': {
            'Meta': {'object_name': 'Facility'},
            'address': ('django.db.models.fields.CharField', [], {'max_length': '400', 'blank': 'True'}),
            'address_normalized': ('django.db.models.fields.CharField', [], {'max_length': '400', 'blank': 'True'}),
            'contact_email': ('django.db.models.fields.EmailField', [], {'max_length': '60', 'blank': 'True'}),
            'contact_name': ('django.db.models.fields.CharField', [], {'max_length': '60', 'blank': 'True'}),
            'contact_phone': ('django.db.models.fields.CharField', [], {'max_length': '60', 'blank': 'True'}),
            'counter': ('django.db.models.fields.IntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '32', 'primary_key': 'True'}),
            'latitude': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'longitude': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'signature': ('django.db.models.fields.CharField', [], {'max_length': '360', 'null': 'True', 'blank': 'True'}),
            'signed_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['securesync.Device']"}),
            'signed_version': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'user_count': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'zone_fallback': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['securesync.Zone']"}),
            'zoom': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'})
        },
        'securesync.facilitygroup': {
            'Meta': {'object_name': 'FacilityGroup'},
            'counter': ('django.db.models.fields.IntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'facility': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['securesync.Facility']"}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '32', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'signature': ('django.db.models.fields.CharField', [], {'max_length': '360', 'null': 'True', 'blank': 'True'}),
            'signed_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['securesync.Device']"}),
            'signed_version': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'zone_fallback': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['securesync.Zone']"})
        },
        'securesync.facilityuser': {
            'Meta': {'object_name': 'FacilityUser'},
            'counter': ('django.db.models.fields.IntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'default_language': ('django.db.models.fields.CharField', [], {'max_length': '8', 'null': 'True', 'blank': 'True'}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'facility': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['securesync.Facility']"}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['securesync.FacilityGroup']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '32', 'primary_key': 'True'}),
            'is_teacher': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '60', 'blank': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'signature': ('django.db.models.fields.CharField', [], {'max_length': '360', 'null': 'True', 'blank': 'True'}),
            'signed_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['securesync.Device']"}),
            'signed_version': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'zone_fallback': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['securesync.Zone']"})
        },
        'securesync.zone': {
            'Meta': {'object_name': 'Zone'},
            'counter': ('django.db.models.fields.IntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '32', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'signature': ('django.db.models.fields.CharField', [], {'max_length': '360', 'null': 'True', 'blank': 'True'}),
            'signed_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['securesync.Device']"}),
            'signed_version': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'zone_fallback': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['securesync.Zone']"})
        },
        u'store.storetransactionlog': {
            'Meta': {'object_name': 'StoreTransactionLog'},
            'context_id': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'context_type': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'counter': ('django.db.models.fields.IntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '32', 'primary_key': 'True'}),
            'item': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'}),
            'purchased_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'reversible': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'signature': ('django.db.models.fields.CharField', [], {'max_length': '360', 'null': 'True', 'blank': 'True'}),
            'signed_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['securesync.Device']"}),
            'signed_version': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['securesync.FacilityUser']"}),
            'value': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'zone_fallback': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['securesync.Zone']"})
        }
    }

    complete_apps = ['store']