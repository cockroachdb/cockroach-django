from django.db.backends.postgresql.features import (
    DatabaseFeatures as PostgresDatabaseFeatures,
)
from django.utils.functional import cached_property


class DatabaseFeatures(PostgresDatabaseFeatures):
    minimum_database_version = (23, 1)

    # Cloning databases doesn't speed up tests.
    # https://github.com/cockroachdb/django-cockroachdb/issues/206
    can_clone_databases = False

    # Not supported: https://github.com/cockroachdb/cockroach/issues/31632
    can_defer_constraint_checks = False

    # Not supported: https://github.com/cockroachdb/cockroach/issues/48307
    supports_deferrable_unique_constraints = False

    # There are limitations on having DDL statements in a transaction:
    # https://www.cockroachlabs.com/docs/stable/known-limitations.html#schema-changes-within-transactions
    can_rollback_ddl = False

    # Not supported: https://github.com/cockroachdb/cockroach/issues/17511
    create_test_procedure_without_params_sql = None
    create_test_procedure_with_int_param_sql = None

    # Sequences on AutoField don't begin (or reset) to 1 like other databases
    # due to use of DEFAULT unique_rowid().
    supports_sequence_reset = False

    # Forward references in fixtures won't work until cockroachdb can
    # disable constraints: https://github.com/cockroachdb/cockroach/issues/19444
    supports_forward_references = False

    # Unlike PostgreSQL, cockroachdb doesn't support any EXPLAIN formats
    # ('JSON', 'TEXT', 'XML', and 'YAML').
    supported_explain_formats = set()

    # Not supported: https://github.com/cockroachdb/cockroach/issues/41645
    supports_regex_backreferencing = False

    # CockroachDB sorts NULL values first with ASC and last with DESC.
    # PostgreSQL behaves the opposite.
    nulls_order_largest = False

    # pg_catalog.obj_description is very slow:
    # https://github.com/cockroachdb/cockroach/issues/95068
    supports_comments = False

    @cached_property
    def introspected_field_types(self):
        return {
            **super().introspected_field_types,
            'AutoField': 'BigIntegerField',
            'BigAutoField': 'BigIntegerField',
            'IntegerField': 'BigIntegerField',
            'PositiveIntegerField': 'BigIntegerField',
            'SmallAutoField': 'SmallIntegerField',
        }

    # CockroachDB doesn't create indexes on foreign keys.
    indexes_foreign_keys = False

    # Not supported: https://github.com/cockroachdb/cockroach/issues/59567
    supports_non_deterministic_collations = False

    test_collations = {
        # PostgresDatabaseFeatures uses 'sv-x-icu' for 'non_default' but
        # CockroachDB doesn't introspect that properly:
        # https://github.com/cockroachdb/cockroach/issues/54817
        'non_default': 'sv',
        'swedish_ci': 'sv-x-icu',
        # Not supported: https://github.com/cockroachdb/cockroach/issues/111091
        'virtual': None,
    }

    @cached_property
    def is_cockroachdb_23_2(self):
        return self.connection.cockroachdb_version >= (23, 2)

    @cached_property
    def is_cockroachdb_24_1(self):
        return self.connection.cockroachdb_version >= (24, 1)

    @cached_property
    def is_cockroachdb_24_3(self):
        return self.connection.cockroachdb_version >= (24, 3)

    @cached_property
    def is_cockroachdb_25_1(self):
        return self.connection.cockroachdb_version >= (25, 1)

    @cached_property
    def django_test_expected_failures(self):
        expected_failures = super().django_test_expected_failures
        expected_failures.update({
            # sum(): unsupported binary operator: <float> + <int>:
            # https://github.com/cockroachdb/django-cockroachdb/issues/73
            'aggregation.tests.AggregateTestCase.test_add_implementation',
            'aggregation.tests.AggregateTestCase.test_combine_different_types',
            'expressions.tests.ExpressionsNumericTests.test_complex_expressions',
            # greatest(): expected avg(price) to be of type float, found type
            # decimal: https://github.com/cockroachdb/django-cockroachdb/issues/74
            'aggregation.tests.AggregateTestCase.test_expression_on_aggregation',
            # POWER() doesn't support negative exponents:
            # https://github.com/cockroachdb/django-cockroachdb/issues/22
            'db_functions.math.test_power.PowerTests.test_integer',
            # Tests that assume a serial pk: https://github.com/cockroachdb/django-cockroachdb/issues/18
            'multiple_database.tests.RouterTestCase.test_generic_key_cross_database_protection',
            # Unsupported query: mixed type addition in SELECT:
            # https://github.com/cockroachdb/django-cockroachdb/issues/19
            'annotations.tests.NonAggregateAnnotationTestCase.test_mixed_type_annotation_numbers',
            # Forward references in fixtures won't work until CockroachDB can
            # disable constraints: https://github.com/cockroachdb/cockroach/issues/19444
            'backends.base.test_creation.TestDeserializeDbFromString.test_circular_reference',
            'backends.base.test_creation.TestDeserializeDbFromString.test_circular_reference_with_natural_key',
            'backends.base.test_creation.TestDeserializeDbFromString.test_self_reference',
            'fixtures.tests.CircularReferenceTests.test_circular_reference',
            'fixtures.tests.ForwardReferenceTests.test_forward_reference_fk',
            'fixtures.tests.ForwardReferenceTests.test_forward_reference_m2m',
            'serializers.test_data.SerializerDataTests.test_json_serializer',
            'serializers.test_data.SerializerDataTests.test_jsonl_serializer',
            'serializers.test_data.SerializerDataTests.test_python_serializer',
            'serializers.test_data.SerializerDataTests.test_xml_serializer',
            'serializers.test_data.SerializerDataTests.test_yaml_serializer',
            # No sequence for AutoField in CockroachDB.
            'introspection.tests.IntrospectionTests.test_sequence_list',
            # CockroachDB doesn't support disabling constraints:
            # https://github.com/cockroachdb/cockroach/issues/19444
            'auth_tests.test_views.UUIDUserTests.test_admin_password_change',
            'backends.tests.FkConstraintsTests.test_check_constraints',
            'backends.tests.FkConstraintsTests.test_check_constraints_sql_keywords',
            'backends.tests.FkConstraintsTests.test_disable_constraint_checks_context_manager',
            'backends.tests.FkConstraintsTests.test_disable_constraint_checks_manually',
            # SchemaEditor._model_indexes_sql() doesn't output some expected
            # tablespace SQL because CockroachDB automatically indexes foreign
            # keys.
            'model_options.test_tablespaces.TablespacesTests.test_tablespace_for_many_to_many_field',
            # ALTER COLUMN TYPE requiring rewrite of on-disk data is currently
            # not supported for columns that are part of an index.
            # https://go.crdb.dev/issue/47636
            'migrations.test_executor.ExecutorTests.test_alter_id_type_with_fk',
            'migrations.test_operations.OperationTests.test_alter_field_pk_fk',
            'migrations.test_operations.OperationTests.test_alter_field_pk_fk_char_to_int',
            'migrations.test_operations.OperationTests.test_alter_field_pk_fk_db_collation',
            'migrations.test_operations.OperationTests.test_alter_field_reloads_state_fk_with_to_field_related_name_target_type_change',  # noqa
            'migrations.test_operations.OperationTests.test_alter_field_reloads_state_on_fk_with_to_field_target_type_change',  # noqa
            'schema.tests.SchemaTests.test_alter_auto_field_to_char_field',
            'schema.tests.SchemaTests.test_alter_autofield_pk_to_smallautofield_pk',
            'schema.tests.SchemaTests.test_alter_primary_key_db_collation',
            'schema.tests.SchemaTests.test_char_field_pk_to_auto_field',
            'schema.tests.SchemaTests.test_char_field_with_db_index_to_fk',
            'schema.tests.SchemaTests.test_text_field_with_db_index_to_fk',
            # CockroachDB doesn't support dropping the primary key.
            'schema.tests.SchemaTests.test_alter_int_pk_to_int_unique',
            # CockroachDB doesn't support changing the primary key of table.
            # psycopg.errors.InvalidColumnReference: column "id" is referenced
            # by the primary key
            'migrations.test_operations.OperationTests.test_alter_id_pk_to_uuid_pk',
            'schema.tests.SchemaTests.test_alter_not_unique_field_to_primary_key',
            'schema.tests.SchemaTests.test_primary_key',
            # SmallAutoField doesn't work:
            # https://github.com/cockroachdb/cockroach-django/issues/84
            'bulk_create.tests.BulkCreateTests.test_bulk_insert_nullable_fields',
            'many_to_one.tests.ManyToOneTests.test_add_remove_set_by_pk_raises',
            'many_to_one.tests.ManyToOneTests.test_fk_to_smallautofield',
            'many_to_one.tests.ManyToOneTests.test_get_prefetch_queryset_reverse_warning',
            'many_to_one.tests.ManyToOneTests.test_get_prefetch_querysets_reverse_invalid_querysets_length',
            'migrations.test_operations.OperationTests.test_smallfield_autofield_foreignfield_growth',
            'migrations.test_operations.OperationTests.test_smallfield_bigautofield_foreignfield_growth',
            # unexpected unique index in pg_constraint query:
            # https://github.com/cockroachdb/cockroach/issues/61098
            'introspection.tests.IntrospectionTests.test_get_constraints_unique_indexes_orders',
            'schema.tests.SchemaTests.test_func_unique_constraint',
            'schema.tests.SchemaTests.test_func_unique_constraint_collate',
            'schema.tests.SchemaTests.test_func_unique_constraint_covering',
            'schema.tests.SchemaTests.test_unique_constraint_field_and_expression',
            # unimplemented: primary key dropped without subsequent addition of
            # new primary key in same transaction
            'schema.tests.SchemaTests.test_add_auto_field',
            'schema.tests.SchemaTests.test_autofield_to_o2o',
            # incompatible COALESCE expressions: unsupported binary operator:
            # <int> * <int> (desired <decimal>):
            # https://github.com/cockroachdb/cockroach/issues/73587
            'aggregation.tests.AggregateTestCase.test_aggregation_default_expression',
            # ProgrammingError: VALUES types int and float cannot be matched
            'field_defaults.tests.DefaultTests.test_bulk_create_mixed_db_defaults_function',
        })
        if not self.is_cockroachdb_24_3:
            expected_failures.update({
                # ALTER COLUMN TYPE requiring rewrite of on-disk data is currently
                # not supported for columns that are part of an index.
                # https://go.crdb.dev/issue/47636
                'schema.tests.SchemaTests.test_alter_primary_key_the_same_name',
                'migrations.test_operations.OperationTests.test_alter_field_reloads_state_on_fk_target_changes',
                'migrations.test_operations.OperationTests.test_alter_field_reloads_state_on_fk_with_to_field_target_changes',  # noqa
                'migrations.test_operations.OperationTests.test_rename_field_reloads_state_on_fk_target_changes',
                # unknown signature: concat(varchar, int) (returning <string>)
                'migrations.test_operations.OperationTests.test_add_generate_field',
                # concat(): unknown signature: concat(string, int2) (desired <string>)
                'db_functions.text.test_concat.ConcatTests.test_concat_non_str',
            })
        if not self.is_cockroachdb_23_2:
            expected_failures.update({
                # cannot index a json element:
                # https://github.com/cockroachdb/cockroach/issues/35706
                'schema.tests.SchemaTests.test_func_index_json_key_transform',
                # ordering by JSON isn't supported:
                # https://github.com/cockroachdb/cockroach/issues/35706
                'db_functions.comparison.test_json_object.JSONObjectTests.test_order_by_key',
                'db_functions.comparison.test_json_object.JSONObjectTests.test_order_by_nested_key',
                'expressions_window.tests.WindowFunctionTests.test_key_transform',
                'model_fields.test_jsonfield.TestQuerying.test_deep_distinct',
                'model_fields.test_jsonfield.TestQuerying.test_order_grouping_custom_decoder',
                'model_fields.test_jsonfield.TestQuerying.test_ordering_by_transform',
                'model_fields.test_jsonfield.TestQuerying.test_ordering_grouping_by_key_transform',
                # unsupported comparison operator: <jsonb> > <string>:
                # https://github.com/cockroachdb/cockroach/issues/49144
                'model_fields.test_jsonfield.TestQuerying.test_deep_lookup_transform',
                # DataError: incompatible COALESCE expressions: expected pi() to be
                # of type decimal, found type float
                # https://github.com/cockroachdb/cockroach/issues/73587#issuecomment-988408190
                'aggregation.tests.AggregateTestCase.test_aggregation_default_using_decimal_from_database',
            })
        if self.is_cockroachdb_24_1:
            # USING cast required: https://github.com/cockroachdb/cockroach/issues/82416#issuecomment-2029803229
            expected_failures.update({
                'schema.tests.SchemaTests.test_alter_text_field_to_date_field',
                'schema.tests.SchemaTests.test_alter_text_field_to_datetime_field',
                'schema.tests.SchemaTests.test_alter_text_field_to_time_field',
            })
        if self.uses_server_side_binding:
            expected_failures.update({
                # could not determine data type of placeholder:
                # https://github.com/cockroachdb/cockroach/issues/91396
                'backends.tests.EscapingChecks.test_parameter_escaping',
                'backends.tests.EscapingChecksDebug.test_parameter_escaping',
                'constraints.tests.CheckConstraintTests.test_database_default',
                'expressions.tests.BasicExpressionsTests.test_annotate_values_filter',
                'expressions_case.tests.CaseDocumentationExamples.test_lookup_example',
                'expressions_case.tests.CaseDocumentationExamples.test_simple_example',
                'expressions_case.tests.CaseExpressionTests.test_aggregation_empty_cases',
                'expressions_case.tests.CaseExpressionTests.test_annotate',
                'expressions_case.tests.CaseExpressionTests.test_annotate_exclude',
                'expressions_case.tests.CaseExpressionTests.test_annotate_values_not_in_order_by',
                'expressions_case.tests.CaseExpressionTests.test_annotate_with_aggregation_in_condition',
                'expressions_case.tests.CaseExpressionTests.test_annotate_with_aggregation_in_predicate',
                'expressions_case.tests.CaseExpressionTests.test_annotate_with_annotation_in_condition',
                'expressions_case.tests.CaseExpressionTests.test_annotate_with_annotation_in_predicate',
                'expressions_case.tests.CaseExpressionTests.test_annotate_with_empty_when',
                'expressions_case.tests.CaseExpressionTests.test_annotate_with_expression_as_condition',
                'expressions_case.tests.CaseExpressionTests.test_annotate_with_full_when',
                'expressions_case.tests.CaseExpressionTests.test_annotate_with_join_in_condition',
                'expressions_case.tests.CaseExpressionTests.test_annotate_with_join_in_predicate',
                'expressions_case.tests.CaseExpressionTests.test_case_reuse',
                'expressions_case.tests.CaseExpressionTests.test_combined_q_object',
                'expressions_case.tests.CaseExpressionTests.test_lookup_different_fields',
                'expressions_case.tests.CaseExpressionTests.test_lookup_in_condition',
                'expressions_case.tests.CaseExpressionTests.test_update_generic_ip_address',
                'lookup.tests.LookupQueryingTests.test_conditional_expression',
                'ordering.tests.OrderingTests.test_order_by_constant_value',
                'queries.test_bulk_update.BulkUpdateNoteTests.test_batch_size',
                'queries.test_bulk_update.BulkUpdateNoteTests.test_multiple_fields',
                'queries.test_bulk_update.BulkUpdateNoteTests.test_simple',
                'queries.test_bulk_update.BulkUpdateTests.test_custom_pk',
                'queries.test_bulk_update.BulkUpdateTests.test_database_routing',
                'queries.test_bulk_update.BulkUpdateTests.test_database_routing_batch_atomicity',
                'queries.test_bulk_update.BulkUpdateTests.test_falsey_pk_value',
                'queries.test_bulk_update.BulkUpdateTests.test_inherited_fields',
                'queries.test_bulk_update.BulkUpdateTests.test_large_batch',
                'queries.test_bulk_update.BulkUpdateTests.test_updated_rows_when_passing_duplicates',
                'queries.test_q.QCheckTests.test_expression',
                'queries.test_qs_combinators.QuerySetSetOperationTests.test_union_multiple_models_with_values_list_and_annotations',  # noqa
                # error in argument for $2: could not parse ":" as type int2:
                # strconv.ParseInt: parsing ":": invalid syntax
                # https://github.com/cockroachdb/cockroach/issues/136295
                'db_functions.text.test_concat.ConcatTests.test_concat_non_str',
                # unsupported binary operator: <interval> / <decimal>
                'expressions.tests.FTimeDeltaTests.test_durationfield_multiply_divide',
                # InvalidParameterValue: unsupported binary operator: <int4> / <float>
                'queries.tests.Ticket23605Tests.test_ticket_23605',
                # InvalidParameterValue: unsupported binary operator: <int2> + <float>
                'annotations.tests.NonAggregateAnnotationTestCase.test_combined_annotation_commutative',
                # incompatible COALESCE expressions: unsupported binary
                # operator: <decimal> / <float>  (desired <decimal>)
                'aggregation.tests.AggregateTestCase.test_aggregation_default_passed_another_aggregate',
            })
            if self.is_cockroachdb_24_3:
                expected_failures.update({
                    # psycopg.errors.IndeterminateDatatype: replace():
                    # replace(): replace(): concat(): could not determine data
                    # type of placeholder $3. This worked until v24.3 added
                    # support for non-string data to concat():
                    # https://github.com/cockroachdb/cockroach/pull/127098#issuecomment-2492652084
                    "model_fields.test_uuid.TestQuerying.test_filter_with_expr",
                })
            if self.is_cockroachdb_25_1:
                expected_failures.update({
                    'expressions_case.tests.CaseExpressionTests.test_filter_with_expression_as_condition',
                })
        else:
            expected_failures.update({
                # Unsupported query: unsupported binary operator: <int> / <int>:
                # https://github.com/cockroachdb/django-cockroachdb/issues/21
                'expressions.tests.ExpressionOperatorTests.test_lefthand_division',
                'expressions.tests.ExpressionOperatorTests.test_right_hand_division',
            })
        return expected_failures

    @cached_property
    def django_test_skips(self):
        skips = super().django_test_skips
        skips.update({
            # https://github.com/cockroachdb/django-cockroachdb/issues/153#issuecomment-664697963
            'CockroachDB has more restrictive blocking than other databases.': {
                'select_for_update.tests.SelectForUpdateTests.test_block',
            },
            # https://www.cockroachlabs.com/docs/stable/transaction-retry-error-reference.html#retry_write_too_old
            'Fails with TransactionRetryWithProtoRefreshError: ... RETRY_WRITE_TOO_OLD ...': {
                'delete_regress.tests.DeleteLockingTest.test_concurrent_delete',
            },
            'Skip to prevents some error output in the logs.': {
                # Since QuerySet.select_for_update() was enabled, this test is
                # already skipped by the 'Database took too long to lock the row'
                # logic in the test. Skipping it entirely prevents some error
                # output in the logs:
                # Exception in thread Thread-1:
                # ...
                # psycopg.errors.SerializationFailure: restart transaction:
                # TransactionRetryWithProtoRefreshError: WriteTooOldError: write
                # at timestamp 1598314405.858850941,0 too old; wrote at
                # 1598314405.883337663,1
                'get_or_create.tests.UpdateOrCreateTransactionTests.test_creation_in_transaction',
                # Sometimes fails as above or with
                # AssertionError: datetime.timedelta(microseconds=28529) not
                # greater than datetime.timedelta(microseconds=500000)
                'get_or_create.tests.UpdateOrCreateTransactionTests.test_updates_in_transaction',
            },
            # https://www.cockroachlabs.com/docs/stable/transaction-retry-error-reference.html#abort_reason_client_reject
            'Often fails with SerializationFailure: restart transaction: TransactionRetryWithProtoRefreshError': {
                'admin_views.test_multidb.ViewOnSiteTests.test_contenttype_in_separate_db',
            },
        })
        if not self.is_cockroachdb_25_1:
            skips.update({
                # https://github.com/cockroachdb/cockroach/issues/47137
                # These tests only fail sometimes, e.g.
                # https://github.com/cockroachdb/cockroach/issues/65691
                'ALTER COLUMN fails if previous asynchronous ALTER COLUMN has not finished.': {
                    'schema.tests.SchemaTests.test_alter_field_db_collation',
                    'schema.tests.SchemaTests.test_alter_field_type_and_db_collation',
                },
            })
        return skips
