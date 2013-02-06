# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'AssignmentHistory'
        db.create_table('articleflow_assignmenthistory', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='assignment_histories', to=orm['auth.User'])),
            ('article_state', self.gf('django.db.models.fields.related.ForeignKey')(related_name='assignment_histories', to=orm['articleflow.ArticleState'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('last_modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('articleflow', ['AssignmentHistory'])

        # Adding field 'ArticleState.assignee'
        db.add_column('articleflow_articlestate', 'assignee',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['auth.User'], null=True, blank=True),
                      keep_default=False)

        # Adding field 'ArticleExtras.created'
        db.add_column('articleflow_articleextras', 'created',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, default=datetime.datetime(2013, 2, 6, 0, 0), blank=True),
                      keep_default=False)

        # Adding field 'ArticleExtras.last_modified'
        db.add_column('articleflow_articleextras', 'last_modified',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now=True, default=datetime.datetime(2013, 2, 6, 0, 0), blank=True),
                      keep_default=False)

        # Adding M2M table for field worker_groups on 'State'
        db.create_table('articleflow_state_worker_groups', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('state', models.ForeignKey(orm['articleflow.state'], null=False)),
            ('group', models.ForeignKey(orm['auth.group'], null=False))
        ))
        db.create_unique('articleflow_state_worker_groups', ['state_id', 'group_id'])


    def backwards(self, orm):
        # Deleting model 'AssignmentHistory'
        db.delete_table('articleflow_assignmenthistory')

        # Deleting field 'ArticleState.assignee'
        db.delete_column('articleflow_articlestate', 'assignee_id')

        # Deleting field 'ArticleExtras.created'
        db.delete_column('articleflow_articleextras', 'created')

        # Deleting field 'ArticleExtras.last_modified'
        db.delete_column('articleflow_articleextras', 'last_modified')

        # Removing M2M table for field worker_groups on 'State'
        db.delete_table('articleflow_state_worker_groups')


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
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
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
            'assignee': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'from_transition': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'articlestates_created'", 'null': 'True', 'blank': 'True', 'to': "orm['articleflow.Transition']"}),
            'from_transition_user': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'articlestates_created'", 'null': 'True', 'blank': 'True', 'to': "orm['auth.User']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'state': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['articleflow.State']"})
        },
        'articleflow.assignmenthistory': {
            'Meta': {'object_name': 'AssignmentHistory'},
            'article_state': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'assignment_histories'", 'to': "orm['articleflow.ArticleState']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'assignment_histories'", 'to': "orm['auth.User']"})
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
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'worker_groups': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'state_assignments'", 'symmetrical': 'False', 'to': "orm['auth.Group']"})
        },
        'articleflow.transition': {
            'Meta': {'object_name': 'Transition'},
            'allowed_groups': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'allowed_transitions'", 'symmetrical': 'False', 'to': "orm['auth.Group']"}),
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