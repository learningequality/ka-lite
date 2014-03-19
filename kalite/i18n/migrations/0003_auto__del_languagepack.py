# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting model 'LanguagePack'
        db.delete_table('i18n_languagepack')


    def backwards(self, orm):
        # Adding model 'LanguagePack'
        db.create_table('i18n_languagepack', (
            ('code', self.gf('django.db.models.fields.CharField')(max_length=8, primary_key=True)),
            ('approved_translations', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('software_version', self.gf('django.db.models.fields.CharField')(default=None, max_length=20)),
            ('phrases', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('percent_translated', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('subtitle_count', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('language_pack_version', self.gf('django.db.models.fields.PositiveIntegerField')(default=1)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
        ))
        db.send_create_signal('i18n', ['LanguagePack'])


    models = {
        
    }

    complete_apps = ['i18n']