# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'LanguagePack'
        db.create_table('i18n_languagepack', (
            ('code', self.gf('django.db.models.fields.CharField')(max_length=8, primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('phrases', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('approved_translations', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('percent_translated', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('language_pack_version', self.gf('django.db.models.fields.PositiveIntegerField')(default=1)),
            ('software_version', self.gf('django.db.models.fields.CharField')(default=None, max_length=20)),
            ('subtitle_count', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
        ))
        db.send_create_signal('i18n', ['LanguagePack'])


    def backwards(self, orm):
        # Deleting model 'LanguagePack'
        db.delete_table('i18n_languagepack')


    models = {
        'i18n.languagepack': {
            'Meta': {'object_name': 'LanguagePack'},
            'approved_translations': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '8', 'primary_key': 'True'}),
            'language_pack_version': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'percent_translated': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'phrases': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'software_version': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '20'}),
            'subtitle_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'})
        }
    }

    complete_apps = ['i18n']