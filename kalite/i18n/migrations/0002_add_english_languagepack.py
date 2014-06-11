# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

from kalite.version import VERSION


class Migration(SchemaMigration):

    def forwards(self, orm):
        orm["i18n.LanguagePack"].objects.get_or_create(
            code='en',
            defaults={
                'software_version': VERSION,
                'language_pack_version': 0,
                'percent_translated': 100,
                'subtitle_count': 0,
                'name': 'English',
            })

    def backwards(self, orm):
        LanguagePack.objects.filter(code='en').delete()

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
    symmetrical = True
    no_dry_run = True
