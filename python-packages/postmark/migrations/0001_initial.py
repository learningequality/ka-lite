# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'EmailMessage'
        db.create_table('postmark_emailmessage', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('message_id', self.gf('django.db.models.fields.CharField')(max_length=40)),
            ('submitted_at', self.gf('django.db.models.fields.DateTimeField')()),
            ('status', self.gf('django.db.models.fields.CharField')(max_length=150)),
            ('to', self.gf('django.db.models.fields.CharField')(max_length=150)),
            ('to_type', self.gf('django.db.models.fields.CharField')(max_length=3)),
            ('sender', self.gf('django.db.models.fields.CharField')(max_length=150)),
            ('reply_to', self.gf('django.db.models.fields.CharField')(max_length=150)),
            ('subject', self.gf('django.db.models.fields.CharField')(max_length=150)),
            ('tag', self.gf('django.db.models.fields.CharField')(max_length=25)),
            ('text_body', self.gf('django.db.models.fields.TextField')()),
            ('html_body', self.gf('django.db.models.fields.TextField')()),
            ('headers', self.gf('django.db.models.fields.TextField')()),
            ('attachments', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('postmark', ['EmailMessage'])

        # Adding model 'EmailBounce'
        db.create_table('postmark_emailbounce', (
            ('id', self.gf('django.db.models.fields.PositiveIntegerField')(primary_key=True)),
            ('message', self.gf('django.db.models.fields.related.ForeignKey')(related_name='bounces', to=orm['postmark.EmailMessage'])),
            ('inactive', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('can_activate', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('details', self.gf('django.db.models.fields.TextField')()),
            ('bounced_at', self.gf('django.db.models.fields.DateTimeField')()),
            ('_order', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('postmark', ['EmailBounce'])


    def backwards(self, orm):
        
        # Deleting model 'EmailMessage'
        db.delete_table('postmark_emailmessage')

        # Deleting model 'EmailBounce'
        db.delete_table('postmark_emailbounce')


    models = {
        'postmark.emailbounce': {
            'Meta': {'ordering': "('_order',)", 'object_name': 'EmailBounce'},
            '_order': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'bounced_at': ('django.db.models.fields.DateTimeField', [], {}),
            'can_activate': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'details': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.PositiveIntegerField', [], {'primary_key': 'True'}),
            'inactive': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'message': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'bounces'", 'to': "orm['postmark.EmailMessage']"}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'postmark.emailmessage': {
            'Meta': {'ordering': "['-submitted_at']", 'object_name': 'EmailMessage'},
            'attachments': ('django.db.models.fields.TextField', [], {}),
            'headers': ('django.db.models.fields.TextField', [], {}),
            'html_body': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message_id': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'reply_to': ('django.db.models.fields.CharField', [], {'max_length': '150'}),
            'sender': ('django.db.models.fields.CharField', [], {'max_length': '150'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '150'}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '150'}),
            'submitted_at': ('django.db.models.fields.DateTimeField', [], {}),
            'tag': ('django.db.models.fields.CharField', [], {'max_length': '25'}),
            'text_body': ('django.db.models.fields.TextField', [], {}),
            'to': ('django.db.models.fields.CharField', [], {'max_length': '150'}),
            'to_type': ('django.db.models.fields.CharField', [], {'max_length': '3'})
        }
    }

    complete_apps = ['postmark']
