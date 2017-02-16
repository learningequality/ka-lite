# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'SyncSession'
        db.create_table('securesync_syncsession', (
            ('client_nonce', self.gf('django.db.models.fields.CharField')(max_length=32, primary_key=True)),
            ('client_device', self.gf('django.db.models.fields.related.ForeignKey')(related_name='client_sessions', to=orm['securesync.Device'])),
            ('server_nonce', self.gf('django.db.models.fields.CharField')(max_length=32, blank=True)),
            ('server_device', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='server_sessions', null=True, to=orm['securesync.Device'])),
            ('verified', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('ip', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('models_uploaded', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('models_downloaded', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('closed', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('securesync', ['SyncSession'])

        # Adding model 'RegisteredDevicePublicKey'
        db.create_table('securesync_registereddevicepublickey', (
            ('public_key', self.gf('django.db.models.fields.CharField')(max_length=500)),
            ('zone', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['securesync.Zone'])),
        ))
        db.send_create_signal('securesync', ['RegisteredDevicePublicKey'])

        # Adding model 'DeviceMetadata'
        db.create_table('securesync_devicemetadata', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('device', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['securesync.Device'], unique=True, null=True, blank=True)),
            ('is_trusted', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('is_own_device', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('counter_position', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('securesync', ['DeviceMetadata'])

        # Adding model 'Zone'
        db.create_table('securesync_zone', (
            ('id', self.gf('django.db.models.fields.CharField')(max_length=32, primary_key=True)),
            ('counter', self.gf('django.db.models.fields.IntegerField')()),
            ('signature', self.gf('django.db.models.fields.CharField')(max_length=360, blank=True)),
            ('signed_version', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('signed_by', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', null=True, to=orm['securesync.Device'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('securesync', ['Zone'])

        # Adding model 'Facility'
        db.create_table('securesync_facility', (
            ('id', self.gf('django.db.models.fields.CharField')(max_length=32, primary_key=True)),
            ('counter', self.gf('django.db.models.fields.IntegerField')()),
            ('signature', self.gf('django.db.models.fields.CharField')(max_length=360, blank=True)),
            ('signed_version', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('signed_by', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', null=True, to=orm['securesync.Device'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('address', self.gf('django.db.models.fields.CharField')(max_length=400, blank=True)),
            ('address_normalized', self.gf('django.db.models.fields.CharField')(max_length=400, blank=True)),
            ('latitude', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('longitude', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
        ))
        db.send_create_signal('securesync', ['Facility'])

        # Adding model 'FacilityUser'
        db.create_table('securesync_facilityuser', (
            ('id', self.gf('django.db.models.fields.CharField')(max_length=32, primary_key=True)),
            ('counter', self.gf('django.db.models.fields.IntegerField')()),
            ('signature', self.gf('django.db.models.fields.CharField')(max_length=360, blank=True)),
            ('signed_version', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('signed_by', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', null=True, to=orm['securesync.Device'])),
            ('facility', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['securesync.Facility'])),
            ('username', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('first_name', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('last_name', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('notes', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('password', self.gf('django.db.models.fields.CharField')(max_length=128)),
        ))
        db.send_create_signal('securesync', ['FacilityUser'])

        # Adding unique constraint on 'FacilityUser', fields ['facility', 'username']
        db.create_unique('securesync_facilityuser', ['facility_id', 'username'])

        # Adding model 'DeviceZone'
        db.create_table('securesync_devicezone', (
            ('id', self.gf('django.db.models.fields.CharField')(max_length=32, primary_key=True)),
            ('counter', self.gf('django.db.models.fields.IntegerField')()),
            ('signature', self.gf('django.db.models.fields.CharField')(max_length=360, blank=True)),
            ('signed_version', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('signed_by', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', null=True, to=orm['securesync.Device'])),
            ('device', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['securesync.Device'], unique=True)),
            ('zone', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['securesync.Zone'])),
        ))
        db.send_create_signal('securesync', ['DeviceZone'])

        # Adding model 'Device'
        db.create_table('securesync_device', (
            ('id', self.gf('django.db.models.fields.CharField')(max_length=32, primary_key=True)),
            ('counter', self.gf('django.db.models.fields.IntegerField')()),
            ('signature', self.gf('django.db.models.fields.CharField')(max_length=360, blank=True)),
            ('signed_version', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('signed_by', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', null=True, to=orm['securesync.Device'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('public_key', self.gf('django.db.models.fields.CharField')(max_length=200, db_index=True)),
        ))
        db.send_create_signal('securesync', ['Device'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'FacilityUser', fields ['facility', 'username']
        db.delete_unique('securesync_facilityuser', ['facility_id', 'username'])

        # Deleting model 'SyncSession'
        db.delete_table('securesync_syncsession')

        # Deleting model 'RegisteredDevicePublicKey'
        db.delete_table('securesync_registereddevicepublickey')

        # Deleting model 'DeviceMetadata'
        db.delete_table('securesync_devicemetadata')

        # Deleting model 'Zone'
        db.delete_table('securesync_zone')

        # Deleting model 'Facility'
        db.delete_table('securesync_facility')

        # Deleting model 'FacilityUser'
        db.delete_table('securesync_facilityuser')

        # Deleting model 'DeviceZone'
        db.delete_table('securesync_devicezone')

        # Deleting model 'Device'
        db.delete_table('securesync_device')


    models = {
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
        'securesync.devicemetadata': {
            'Meta': {'object_name': 'DeviceMetadata'},
            'counter_position': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'device': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['securesync.Device']", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_own_device': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_trusted': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'securesync.devicezone': {
            'Meta': {'object_name': 'DeviceZone'},
            'counter': ('django.db.models.fields.IntegerField', [], {}),
            'device': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['securesync.Device']", 'unique': 'True'}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '32', 'primary_key': 'True'}),
            'signature': ('django.db.models.fields.CharField', [], {'max_length': '360', 'blank': 'True'}),
            'signed_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['securesync.Device']"}),
            'signed_version': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'zone': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['securesync.Zone']"})
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
        },
        'securesync.registereddevicepublickey': {
            'Meta': {'object_name': 'RegisteredDevicePublicKey'},
            'public_key': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'zone': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['securesync.Zone']"})
        },
        'securesync.syncsession': {
            'Meta': {'object_name': 'SyncSession'},
            'client_device': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'client_sessions'", 'to': "orm['securesync.Device']"}),
            'client_nonce': ('django.db.models.fields.CharField', [], {'max_length': '32', 'primary_key': 'True'}),
            'closed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'ip': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'models_downloaded': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'models_uploaded': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'server_device': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'server_sessions'", 'null': 'True', 'to': "orm['securesync.Device']"}),
            'server_nonce': ('django.db.models.fields.CharField', [], {'max_length': '32', 'blank': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'verified': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'securesync.zone': {
            'Meta': {'object_name': 'Zone'},
            'counter': ('django.db.models.fields.IntegerField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '32', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'signature': ('django.db.models.fields.CharField', [], {'max_length': '360', 'blank': 'True'}),
            'signed_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['securesync.Device']"}),
            'signed_version': ('django.db.models.fields.IntegerField', [], {'default': '1'})
        }
    }

    complete_apps = ['securesync']
