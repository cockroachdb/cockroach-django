import os
import subprocess
import sys
from unittest import expectedFailure, skip

from django.conf import settings
from django.db.backends.postgresql.creation import (
    DatabaseCreation as PostgresDatabaseCreation,
)
from django.utils.module_loading import import_string

from .client import DatabaseClient


class DatabaseCreation(PostgresDatabaseCreation):

    def mark_expected_failures(self):
        """Mark tests that don't work on cockroachdb as expected failures."""
        expected_failures = (
            # column must appear in the GROUP BY clause or be used in an aggregate function:
            # https://github.com/cockroachdb/cockroach-django/issues/13
            'aggregation.test_filter_argument.FilteredAggregateTests.test_filtered_aggregate_on_annotate',
            'aggregation.test_filter_argument.FilteredAggregateTests.test_filtered_reused_subquery',
            'aggregation.test_filter_argument.FilteredAggregateTests.test_plain_annotate',
            'aggregation.tests.AggregateTestCase.test_annotate_basic',
            'aggregation.tests.AggregateTestCase.test_annotate_defer',
            'aggregation.tests.AggregateTestCase.test_annotate_defer_select_related',
            'aggregation.tests.AggregateTestCase.test_annotate_m2m',
            'aggregation.tests.AggregateTestCase.test_annotate_over_annotate',
            'aggregation.tests.AggregateTestCase.test_annotate_values',
            'aggregation.tests.AggregateTestCase.test_annotate_values_list',
            'aggregation.tests.AggregateTestCase.test_annotation',
            'aggregation.tests.AggregateTestCase.test_annotation_expressions',
            'aggregation.tests.AggregateTestCase.test_backwards_m2m_annotate',
            'aggregation.tests.AggregateTestCase.test_even_more_aggregate',
            'aggregation.tests.AggregateTestCase.test_filtering',
            'aggregation.tests.AggregateTestCase.test_fkey_aggregate',
            'aggregation.tests.AggregateTestCase.test_more_aggregation',
            'aggregation.tests.AggregateTestCase.test_nonfield_annotation',
            'aggregation.tests.AggregateTestCase.test_reverse_fkey_annotate',
            'aggregation.tests.AggregateTestCase.test_ticket17424',
            'aggregation_regress.tests.AggregationTests.test_aggregate_annotation',
            'aggregation_regress.tests.AggregationTests.test_aggregate_duplicate_columns',
            'aggregation_regress.tests.AggregationTests.test_aggregate_duplicate_columns_only',
            'aggregation_regress.tests.AggregationTests.test_aggregate_duplicate_columns_select_related',
            'aggregation_regress.tests.AggregationTests.test_aggregate_fexpr',
            'aggregation_regress.tests.AggregationTests.test_aggregate_ummanaged_model_columns',
            'aggregation_regress.tests.AggregationTests.test_aggregation_with_generic_reverse_relation',
            'aggregation_regress.tests.AggregationTests.test_annotate_joins',
            'aggregation_regress.tests.AggregationTests.test_annotate_on_relation',
            'aggregation_regress.tests.AggregationTests.test_annotate_with_extra',
            'aggregation_regress.tests.AggregationTests.test_annotated_conditional_aggregate',
            'aggregation_regress.tests.AggregationTests.test_annotation',
            'aggregation_regress.tests.AggregationTests.test_annotation_disjunction',
            'aggregation_regress.tests.AggregationTests.test_boolean_conversion',
            'aggregation_regress.tests.AggregationTests.test_db_col_table',
            'aggregation_regress.tests.AggregationTests.test_decimal_aggregate_annotation_filter',
            'aggregation_regress.tests.AggregationTests.test_empty',
            'aggregation_regress.tests.AggregationTests.test_f_expression_annotation',
            'aggregation_regress.tests.AggregationTests.test_filtering_by_annotation_name',
            'aggregation_regress.tests.AggregationTests.test_fobj_group_by',
            'aggregation_regress.tests.AggregationTests.test_more',
            'aggregation_regress.tests.AggregationTests.test_more_more',
            'aggregation_regress.tests.AggregationTests.test_name_expressions',
            'aggregation_regress.tests.AggregationTests.test_name_filters',
            'aggregation_regress.tests.AggregationTests.test_negated_aggregation',
            'aggregation_regress.tests.AggregationTests.test_pickle',
            'aggregation_regress.tests.AggregationTests.test_quoting_aggregate_order_by',
            'aggregation_regress.tests.AggregationTests.test_ticket_11293',
            'aggregation_regress.tests.AggregationTests.test_values_annotate_values',
            'aggregation_regress.tests.JoinPromotionTests.test_ticket_21150',
            'aggregation_regress.tests.SelfReferentialFKTests.test_ticket_24748',
            'annotations.tests.NonAggregateAnnotationTestCase.test_aggregate_over_annotation',
            'annotations.tests.NonAggregateAnnotationTestCase.test_annotate_with_aggregation',
            'annotations.tests.NonAggregateAnnotationTestCase.test_annotation_filter_with_subquery',
            'annotations.tests.NonAggregateAnnotationTestCase.test_filter_agg_with_double_f',
            'custom_managers.tests.CustomManagersRegressTestCase.test_refresh_from_db_when_default_manager_filters',
            'custom_managers.tests.CustomManagersRegressTestCase.test_save_clears_annotations_from_base_manager',
            'db_functions.comparison.test_cast.CastTests.test_cast_from_db_datetime_to_date_group_by',
            'defer_regress.tests.DeferAnnotateSelectRelatedTest.test_defer_annotate_select_related',
            'defer_regress.tests.DeferRegressionTest.test_basic',
            'defer_regress.tests.DeferRegressionTest.test_ticket_16409',
            'distinct_on_fields.tests.DistinctOnTests.test_distinct_not_implemented_checks',
            'expressions.test_queryset_values.ValuesExpressionsTests.test_values_expression_group_by',
            'expressions_case.tests.CaseExpressionTests.test_annotate_with_aggregation_in_condition',
            'expressions_case.tests.CaseExpressionTests.test_annotate_with_aggregation_in_predicate',
            'expressions_case.tests.CaseExpressionTests.test_annotate_with_aggregation_in_value',
            'expressions_case.tests.CaseExpressionTests.test_annotate_with_in_clause',
            'expressions_case.tests.CaseExpressionTests.test_filter_with_aggregation_in_condition',
            'expressions_case.tests.CaseExpressionTests.test_filter_with_aggregation_in_predicate',
            'expressions_case.tests.CaseExpressionTests.test_filter_with_aggregation_in_value',
            'expressions_case.tests.CaseExpressionTests.test_m2m_exclude',
            'expressions_case.tests.CaseExpressionTests.test_m2m_reuse',
            'lookup.test_decimalfield.DecimalFieldLookupTests.test_gt',
            'lookup.test_decimalfield.DecimalFieldLookupTests.test_gte',
            'lookup.test_decimalfield.DecimalFieldLookupTests.test_lt',
            'lookup.test_decimalfield.DecimalFieldLookupTests.test_lte',
            'queries.tests.Queries1Tests.test_ticket_20250',
            'queries.tests.ValuesQuerysetTests.test_named_values_list_with_fields',
            'queries.tests.ValuesQuerysetTests.test_named_values_list_without_fields',
            'queries.test_explain.ExplainTests.test_basic',
            'queryset_pickle.tests.PickleabilityTestCase.test_annotation_with_callable_default',
            'timezones.tests.LegacyDatabaseTests.test_query_annotation',
            'timezones.tests.NewDatabaseTests.test_query_annotation',
            # CAST timestamptz to time doesn't respect active time zone:
            # https://github.com/cockroachdb/cockroach-django/issues/37
            'db_functions.comparison.test_cast.CastTests.test_cast_from_db_datetime_to_time',
            # unknown signature: avg(interval):
            # https://github.com/cockroachdb/cockroach-django/issues/72
            'aggregation.tests.AggregateTestCase.test_avg_duration_field',
            # sum(): unsupported binary operator: <float> + <int>:
            # https://github.com/cockroachdb/cockroach-django/issues/73
            'aggregation.tests.AggregateTestCase.test_add_implementation',
            'aggregation.tests.AggregateTestCase.test_combine_different_types',
            # greatest(): expected avg(price) to be of type float, found type
            # decimal: https://github.com/cockroachdb/cockroach-django/issues/74
            'aggregation.tests.AggregateTestCase.test_expression_on_aggregation',
            # DATE_TRUNC result is incorrectly localized when a timezone is set:
            # https://github.com/cockroachdb/cockroach-django/issues/32
            'admin_views.test_templatetags.DateHierarchyTests.test_choice_links',
            'admin_views.tests.DateHierarchyTests.test_multiple_years',
            'admin_views.tests.DateHierarchyTests.test_related_field',
            'admin_views.tests.DateHierarchyTests.test_single',
            'admin_views.tests.DateHierarchyTests.test_within_month',
            'admin_views.tests.DateHierarchyTests.test_within_year',
            'admin_views.tests.AdminViewBasicTest.test_date_hierarchy_timezone_dst',
            'aggregation.tests.AggregateTestCase.test_dates_with_aggregation',
            'aggregation_regress.tests.AggregationTests.test_more_more_more',
            'backends.tests.DateQuotingTest.test_django_date_trunc',
            'dates.tests.DatesTests.test_dates_trunc_datetime_fields',
            'dates.tests.DatesTests.test_related_model_traverse',
            'datetimes.tests.DateTimesTests.test_21432',
            'datetimes.tests.DateTimesTests.test_datetimes_has_lazy_iterator',
            'datetimes.tests.DateTimesTests.test_datetimes_returns_available_dates_for_given_scope_and_given_field',
            'datetimes.tests.DateTimesTests.test_related_model_traverse',
            'db_functions.datetime.test_extract_trunc.DateFunctionTests.test_trunc_day_func',
            'db_functions.datetime.test_extract_trunc.DateFunctionTests.test_trunc_func',
            'db_functions.datetime.test_extract_trunc.DateFunctionTests.test_trunc_subquery_with_parameters',
            'db_functions.datetime.test_extract_trunc.DateFunctionTests.test_trunc_month_func',
            'db_functions.datetime.test_extract_trunc.DateFunctionTests.test_trunc_quarter_func',
            'db_functions.datetime.test_extract_trunc.DateFunctionTests.test_trunc_time_func',
            'db_functions.datetime.test_extract_trunc.DateFunctionTests.test_trunc_week_func',
            'db_functions.datetime.test_extract_trunc.DateFunctionTests.test_trunc_year_func',
            'generic_views.test_dates.MonthArchiveViewTests.test_month_view',
            'generic_views.test_dates.MonthArchiveViewTests.test_month_view_allow_future',
            'generic_views.test_dates.MonthArchiveViewTests.test_month_view_get_month_from_request',
            'generic_views.test_dates.YearArchiveViewTests.test_year_view',
            'generic_views.test_dates.YearArchiveViewTests.test_year_view_allow_future',
            'generic_views.test_dates.YearArchiveViewTests.test_year_view_custom_sort_order',
            'generic_views.test_dates.YearArchiveViewTests.test_year_view_make_object_list',
            'generic_views.test_dates.YearArchiveViewTests.test_year_view_two_custom_sort_orders',
            # Because DateFunctionWithTimeZoneTests inherits DateFunctionTests,
            # these tests give "unexpected successes when they pass in the
            # superclass.
            'db_functions.datetime.test_extract_trunc.DateFunctionWithTimeZoneTests.test_trunc_func',
            'db_functions.datetime.test_extract_trunc.DateFunctionWithTimeZoneTests.test_trunc_func_with_timezone',
            'db_functions.datetime.test_extract_trunc.DateFunctionWithTimeZoneTests.test_trunc_week_func',
            'db_functions.datetime.test_extract_trunc.DateFunctionWithTimeZoneTests.test_trunc_hour_func',
            'db_functions.datetime.test_extract_trunc.DateFunctionWithTimeZoneTests.test_trunc_minute_func',
            'db_functions.datetime.test_extract_trunc.DateFunctionWithTimeZoneTests.test_trunc_second_func',
            'db_functions.datetime.test_extract_trunc.DateFunctionWithTimeZoneTests.test_trunc_timezone_applied_before_truncation',  # noqa
            'extra_regress.tests.ExtraRegressTests.test_dates_query',
            'many_to_one.tests.ManyToOneTests.test_select_related',
            'model_inheritance_regress.tests.ModelInheritanceTest.test_issue_7105',
            'model_regress.tests.ModelTests.test_date_filter_null',
            'multiple_database.tests.QueryTestCase.test_basic_queries',
            'queries.tests.Queries1Tests.test_ticket7155',
            'queries.tests.Queries1Tests.test_tickets_6180_6203',
            'queries.tests.Queries1Tests.test_tickets_7087_12242',
            'reserved_names.tests.ReservedNameTests.test_dates',
            'timezones.tests.LegacyDatabaseTests.test_query_datetime_lookups',
            'timezones.tests.LegacyDatabaseTests.test_query_datetimes',
            'timezones.tests.NewDatabaseTests.test_query_datetimes',
            'timezones.tests.NewDatabaseTests.test_query_datetimes_in_other_timezone',
            # stddev/variance functions not supported:
            # https://github.com/cockroachdb/cockroach-django/issues/25
            'aggregation.test_filter_argument.FilteredAggregateTests.test_filtered_numerical_aggregates',
            'aggregation_regress.tests.AggregationTests.test_stddev',
            # POWER() doesn't support negative exponents:
            # https://github.com/cockroachdb/cockroach-django/issues/22
            'db_functions.math.test_power.PowerTests.test_integer',
            # Unsupported query: unknown signature: extract(string, interval)
            # https://github.com/cockroachdb/cockroach-django/issues/29
            'db_functions.datetime.test_extract_trunc.DateFunctionTests.test_extract_duration',
            'db_functions.datetime.test_extract_trunc.DateFunctionWithTimeZoneTests.test_extract_duration',
            # extract(): unsupported timespan: isoyear:
            # https://github.com/cockroachdb/cockroach-django/issues/28
            'db_functions.datetime.test_extract_trunc.DateFunctionTests.test_extract_iso_year_func',
            'db_functions.datetime.test_extract_trunc.DateFunctionTests.test_extract_iso_year_func_boundaries',
            'db_functions.datetime.test_extract_trunc.DateFunctionWithTimeZoneTests.test_extract_func_with_timezone',
            'db_functions.datetime.test_extract_trunc.DateFunctionWithTimeZoneTests.test_extract_iso_year_func',
            'db_functions.datetime.test_extract_trunc.DateFunctionWithTimeZoneTests.test_extract_iso_year_func_boundaries',  # noqa
            # extract() doesn't respect active time zone:
            # https://github.com/cockroachdb/cockroach-django/issues/47
            'db_functions.datetime.test_extract_trunc.DateFunctionTests.test_extract_func',
            'db_functions.datetime.test_extract_trunc.DateFunctionTests.test_extract_hour_func',
            # Tests that assume a serial pk: https://github.com/cockroachdb/cockroach-django/issues/18
            'admin_views.tests.AdminViewPermissionsTest.test_history_view',
            'defer_regress.tests.DeferRegressionTest.test_ticket_23270',
            'distinct_on_fields.tests.DistinctOnTests.test_basic_distinct_on',
            'generic_relations_regress.tests.GenericRelationTests.test_annotate',
            'model_formsets_regress.tests.FormfieldShouldDeleteFormTests.test_custom_delete',
            'multiple_database.tests.RouterTestCase.test_generic_key_cross_database_protection',
            'ordering.tests.OrderingTests.test_order_by_fk_attname',
            'ordering.tests.OrderingTests.test_order_by_pk',
            'queries.test_bulk_update.BulkUpdateNoteTests.test_multiple_fields',
            'queries.test_bulk_update.BulkUpdateTests.test_inherited_fields',
            'queries.tests.Queries1Tests.test_ticket9411',
            'queries.tests.Ticket14056Tests.test_ticket_14056',
            'queries.tests.RelatedLookupTypeTests.test_values_queryset_lookup',
            'syndication_tests.tests.SyndicationFeedTest.test_rss2_feed',
            'syndication_tests.tests.SyndicationFeedTest.test_latest_post_date',
            'syndication_tests.tests.SyndicationFeedTest.test_rss091_feed',
            'syndication_tests.tests.SyndicationFeedTest.test_template_feed',
            # Transaction issues: https://github.com/cockroachdb/cockroach-django/issues/14
            'delete_regress.tests.DeleteLockingTest.test_concurrent_delete',
            # Tests that require savepoints:
            'admin_views.tests.AdminViewBasicTest.test_disallowed_to_field',
            'admin_views.tests.AdminViewPermissionsTest.test_add_view',
            'admin_views.tests.AdminViewPermissionsTest.test_change_view',
            'admin_views.tests.AdminViewPermissionsTest.test_change_view_save_as_new',
            'admin_views.tests.AdminViewPermissionsTest.test_delete_view',
            'admin_views.tests.GroupAdminTest.test_group_permission_performance',
            'admin_views.tests.UserAdminTest.test_user_permission_performance',
            'auth_tests.test_migrations.ProxyModelWithSameAppLabelTests.test_migrate_with_existing_target_permission',
            'fixtures.tests.FixtureLoadingTests.test_loaddata_app_option',
            'fixtures.tests.FixtureLoadingTests.test_unmatched_identifier_loading',
            'fixtures_model_package.tests.FixtureTestCase.test_loaddata',
            'force_insert_update.tests.ForceTests.test_force_update',
            'get_or_create.tests.GetOrCreateTests.test_get_or_create_invalid_params',
            'get_or_create.tests.GetOrCreateTestsWithManualPKs.test_create_with_duplicate_primary_key',
            'get_or_create.tests.GetOrCreateTestsWithManualPKs.test_get_or_create_raises_IntegrityError_plus_traceback', # noqa
            'get_or_create.tests.GetOrCreateTestsWithManualPKs.test_savepoint_rollback',
            'get_or_create.tests.GetOrCreateThroughManyToMany.test_something',
            'get_or_create.tests.UpdateOrCreateTests.test_integrity',
            'get_or_create.tests.UpdateOrCreateTests.test_manual_primary_key_test',
            'get_or_create.tests.UpdateOrCreateTestsWithManualPKs.test_create_with_duplicate_primary_key',
            'many_to_one.tests.ManyToOneTests.test_fk_assignment_and_related_object_cache',
            'many_to_many.tests.ManyToManyTests.test_add',
            'model_fields.test_booleanfield.BooleanFieldTests.test_null_default',
            'model_fields.test_floatfield.TestFloatField.test_float_validates_object',
            'multiple_database.tests.QueryTestCase.test_generic_key_cross_database_protection',
            'multiple_database.tests.QueryTestCase.test_m2m_cross_database_protection',
            'transaction_hooks.tests.TestConnectionOnCommit.test_discards_hooks_from_rolled_back_savepoint',
            'transaction_hooks.tests.TestConnectionOnCommit.test_inner_savepoint_rolled_back_with_outer',
            'transaction_hooks.tests.TestConnectionOnCommit.test_inner_savepoint_does_not_affect_outer',
            # Unsupported query: mixed type addition in SELECT:
            # https://github.com/cockroachdb/cockroach-django/issues/19
            'annotations.tests.NonAggregateAnnotationTestCase.test_mixed_type_annotation_numbers',
            # Nondeterministic query: https://github.com/cockroachdb/cockroach-django/issues/48
            'queries.tests.SubqueryTests.test_slice_subquery_and_query',
            # log(b, x) not supported: https://github.com/cockroachdb/cockroach-django/issues/50
            'db_functions.math.test_log.LogTests.test_decimal',
            'db_functions.math.test_log.LogTests.test_float',
            'db_functions.math.test_log.LogTests.test_integer',
            'db_functions.math.test_log.LogTests.test_null',
            # Forward references in fixtures won't work until cockroachdb can
            # disable constraints: https://github.com/cockroachdb/cockroach/issues/19444
            'fixtures_regress.tests.TestFixtures.test_loaddata_forward_refs_split_fixtures',
            'fixtures_regress.tests.TestFixtures.test_loaddata_works_when_fixture_has_forward_refs',
            'serializers.test_json.JsonSerializerTransactionTestCase.test_forward_refs',
            'serializers.test_data.SerializerDataTests.test_json_serializer',
            'serializers.test_data.SerializerDataTests.test_python_serializer',
            'serializers.test_data.SerializerDataTests.test_xml_serializer',
            'serializers.test_data.SerializerDataTests.test_yaml_serializer',
            'serializers.test_xml.XmlSerializerTransactionTestCase.test_forward_refs',
            'serializers.test_yaml.YamlSerializerTransactionTestCase.test_forward_refs',
            # cockroachdb doesn't distinguish between tables and views. Both
            # are included regardless of whether inspectdb's --include-views
            # option is set.
            'inspectdb.tests.InspectDBTransactionalTests.test_include_views',
            'introspection.tests.IntrospectionTests.test_table_names_with_views',
            # No sequence for AutoField in cockroachdb.
            'introspection.tests.IntrospectionTests.test_sequence_list',
            # CharField max_length is ignored on cockroachdb. CharField is
            # introspected as TextField.
            'introspection.tests.IntrospectionTests.test_get_table_description_col_lengths',
            # Unsupported query: unsupported binary operator: <int> / <int>:
            # https://github.com/cockroachdb/cockroach-django/issues/21
            'expressions.tests.ExpressionOperatorTests.test_lefthand_division',
            'expressions.tests.ExpressionOperatorTests.test_right_hand_division',
            # Incorrect interval math on date columns when a time zone is set:
            # https://github.com/cockroachdb/cockroach-django/issues/53
            'expressions.tests.FTimeDeltaTests.test_date_comparison',
            'expressions.tests.FTimeDeltaTests.test_mixed_comparisons1',
            # Interval math across dst works differently from other databases.
            # https://github.com/cockroachdb/cockroach-django/issues/54
            'expressions.tests.FTimeDeltaTests.test_delta_update',
            'expressions.tests.FTimeDeltaTests.test_duration_with_datetime_microseconds',
            # Skipped for PostgreSQL but should be skipped for cockroachdb also:
            # https://github.com/cockroachdb/cockroach-django/issues/57
            'expressions_window.tests.WindowFunctionTests.test_range_n_preceding_and_following',
            # cockroachdb doesn't support disabling constraints:
            # https://github.com/cockroachdb/cockroach/issues/19444
            'auth_tests.test_views.UUIDUserTests.test_admin_password_change',
            'backends.tests.FkConstraintsTests.test_check_constraints',
            'backends.tests.FkConstraintsTests.test_disable_constraint_checks_context_manager',
            'backends.tests.FkConstraintsTests.test_disable_constraint_checks_manually',
            # Passing a naive datetime to cursor.execute() probably can't work
            # on cockroachdb. The value needs a timezone so psycopg2 will cast
            # it to timestamptz rather than timestamp to avoid "value type
            # timestamp doesn't match type timestamptz of column "dt"" but
            # there aren't any hooks to do that.
            'timezones.tests.LegacyDatabaseTests.test_cursor_execute_accepts_naive_datetime',
        )
        for test_name in expected_failures:
            test_case_name, _, method_name = test_name.rpartition('.')
            test_app = test_name.split('.')[0]
            # Importing a test app that isn't installed raises RuntimeError.
            if test_app in settings.INSTALLED_APPS:
                test_case = import_string(test_case_name)
                method = getattr(test_case, method_name)
                setattr(test_case, method_name, expectedFailure(method))

        skip_classes = (
            # Unsupported query: UPDATE float column with integer column:
            # Number.objects.update(float=F('integer')) in setUpTestData(c)
            # https://github.com/cockroachdb/cockroach-django/issues/20
            'expressions.tests.ExpressionsNumericTests',
            # Requires savepoints: https://github.com/cockroachdb/cockroach/issues/10735
            'test_utils.tests.TestBadSetUpTestData',
        )
        for test_class in skip_classes:
            test_module_name, _, test_class_name = test_class.rpartition('.')
            test_app = test_module_name.split('.')[0]
            if test_app in settings.INSTALLED_APPS:
                test_module = import_string(test_module_name)
                klass = getattr(test_module, test_class_name)
                setattr(test_module, test_class_name, skip('unsupported by cockroachdb')(klass))

    def create_test_db(self, *args, **kwargs):
        # This environment variable is set by teamcity-build/runtests.py or
        # by a developer running the tests locally.
        if os.environ.get('RUNNING_COCKROACH_BACKEND_TESTS'):
            self.mark_expected_failures()
        super().create_test_db(*args, **kwargs)

    def _clone_test_db(self, suffix, verbosity, keepdb=False):
        source_database_name = self.connection.settings_dict['NAME']
        target_database_name = self.get_test_db_clone_settings(suffix)['NAME']
        test_db_params = {
            'dbname': self.connection.ops.quote_name(target_database_name),
            'suffix': self.sql_table_creation_suffix(),
        }
        with self._nodb_connection.cursor() as cursor:
            try:
                self._execute_create_test_db(cursor, test_db_params, keepdb)
            except Exception:
                if keepdb:
                    # If the database should be kept, skip everything else.
                    return
                try:
                    if verbosity >= 1:
                        self.log('Destroying old test database for alias %s...' % (
                            self._get_database_display_str(verbosity, target_database_name),
                        ))
                    cursor.execute('DROP DATABASE %(dbname)s' % test_db_params)
                    self._execute_create_test_db(cursor, test_db_params, keepdb)
                except Exception as e:
                    self.log('Got an error recreating the test database: %s' % e)
                    sys.exit(2)
        self._clone_db(source_database_name, target_database_name)

    def _clone_db(self, source_database_name, target_database_name):
        dump_args = DatabaseClient.settings_to_cmd_args(self.connection.settings_dict)[1:]
        dump_cmd = ['cockroach', 'dump', source_database_name,
                    '--dump-mode=schema'] + dump_args
        load_args = DatabaseClient.settings_to_cmd_args(self.connection.settings_dict)[1:]
        load_cmd = ['cockroach', 'sql', '-d', target_database_name] + load_args

        with subprocess.Popen(dump_cmd, stdout=subprocess.PIPE) as dump_proc:
            with subprocess.Popen(load_cmd, stdin=dump_proc.stdout, stdout=subprocess.DEVNULL):
                # Allow dump_proc to receive a SIGPIPE if the load process exits.
                dump_proc.stdout.close()
