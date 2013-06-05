# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Contact'
        db.create_table('contact_contact', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=12)),
            ('email', self.gf('django.db.models.fields.EmailField')(max_length=100)),
            ('org_name', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('org_url', self.gf('django.db.models.fields.URLField')(max_length=200, blank=True)),
            ('contact_date', self.gf('django.db.models.fields.DateField')(auto_now_add=True, blank=True)),
            ('cc_email', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('contact', ['Contact'])

        # Adding model 'Deployment'
        db.create_table('contact_deployment', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('contact', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contact.Contact'])),
            ('countries', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('internet_access', self.gf('django_snippets.multiselect.MultiSelectField')(max_length=100, blank=True)),
            ('hardware_infrastructure', self.gf('django_snippets.multiselect.MultiSelectField')(max_length=100, blank=True)),
            ('facilities', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('low_cost_bundle', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('other', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('contact', ['Deployment'])

        # Adding model 'Support'
        db.create_table('contact_support', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('contact', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contact.Contact'])),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=15)),
            ('issue', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('contact', ['Support'])

        # Adding model 'Contribute'
        db.create_table('contact_contribute', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('contact', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contact.Contact'])),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=15)),
            ('issue', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('contact', ['Contribute'])

        # Adding model 'Info'
        db.create_table('contact_info', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('contact', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contact.Contact'])),
            ('issue', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('contact', ['Info'])


    def backwards(self, orm):
        # Deleting model 'Contact'
        db.delete_table('contact_contact')

        # Deleting model 'Deployment'
        db.delete_table('contact_deployment')

        # Deleting model 'Support'
        db.delete_table('contact_support')

        # Deleting model 'Contribute'
        db.delete_table('contact_contribute')

        # Deleting model 'Info'
        db.delete_table('contact_info')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contact.contact': {
            'Meta': {'object_name': 'Contact'},
            'cc_email': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'contact_date': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'org_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'org_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '12'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'})
        },
        'contact.contribute': {
            'Meta': {'object_name': 'Contribute'},
            'contact': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contact.Contact']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'issue': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '15'})
        },
        'contact.deployment': {
            'Meta': {'object_name': 'Deployment'},
            'contact': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contact.Contact']"}),
            'countries': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'facilities': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'hardware_infrastructure': ('django_snippets.multiselect.MultiSelectField', [], {'max_length': '100', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'internet_access': ('django_snippets.multiselect.MultiSelectField', [], {'max_length': '100', 'blank': 'True'}),
            'low_cost_bundle': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'other': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        },
        'contact.info': {
            'Meta': {'object_name': 'Info'},
            'contact': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contact.Contact']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'issue': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        },
        'contact.support': {
            'Meta': {'object_name': 'Support'},
            'contact': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contact.Contact']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'issue': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '15'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['contact']