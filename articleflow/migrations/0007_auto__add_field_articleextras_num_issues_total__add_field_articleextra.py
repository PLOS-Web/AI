# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'ArticleExtras.num_issues_total'
        db.add_column('articleflow_articleextras', 'num_issues_total',
                      self.gf('django.db.models.fields.IntegerField')(default=0),
                      keep_default=False)

        # Adding field 'ArticleExtras.num_errors_total'
        db.add_column('articleflow_articleextras', 'num_errors_total',
                      self.gf('django.db.models.fields.IntegerField')(default=0),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'ArticleExtras.num_issues_total'
        db.delete_column('articleflow_articleextras', 'num_issues_total')

        # Deleting field 'ArticleExtras.num_errors_total'
        db.delete_column('articleflow_articleextras', 'num_errors_total')


    models = {
        'articleflow.article': {
            'Meta': {'object_name': 'Article'},
            'article_extras': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'article_dont_use'", 'null': 'True', 'blank': 'True', 'to': "orm['articleflow.ArticleExtras']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'current_articlestate': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'current_article'", 'null': 'True', 'blank': 'True', 'to': "orm['articleflow.ArticleState']"}),
            'current_state': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'current_articles'", 'null': 'True', 'blank': 'True', 'to': "orm['articleflow.State']"}),
            'doi': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'journal': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['articleflow.Journal']"}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'pubdate': ('django.db.models.fields.DateField', [], {})
        },
        'articleflow.articleextras': {
            'Meta': {'object_name': 'ArticleExtras'},
            'article': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'article_extras_dont_use'", 'to': "orm['articleflow.Article']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'num_errors': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'num_errors_total': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'num_issues_pdf': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'num_issues_si': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'num_issues_total': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'num_issues_xml': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'num_issues_xmlpdf': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'num_warnings': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'articleflow.articlestate': {
            'Meta': {'object_name': 'ArticleState'},
            'article': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'article_states'", 'to': "orm['articleflow.Article']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'from_transition': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'articlestates_created'", 'null': 'True', 'blank': 'True', 'to': "orm['articleflow.Transition']"}),
            'from_transition_user': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'articlestates_created'", 'null': 'True', 'blank': 'True', 'to': "orm['auth.User']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'state': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['articleflow.State']"})
        },
        'articleflow.journal': {
            'Meta': {'object_name': 'Journal'},
            'full_name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'articleflow.state': {
            'Meta': {'object_name': 'State'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'articleflow.transition': {
            'Meta': {'object_name': 'Transition'},
            'disallow_open_items': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'from_state': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'possible_transitions'", 'to': "orm['articleflow.State']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'preference_weight': ('django.db.models.fields.IntegerField', [], {}),
            'to_state': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'possible_last_transitions'", 'to': "orm['articleflow.State']"})
        },
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
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['articleflow']