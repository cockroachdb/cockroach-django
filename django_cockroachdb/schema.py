from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from django.db.backends.postgresql.schema import (
    DatabaseSchemaEditor as PostgresDatabaseSchemaEditor,
)
from django.db.backends.utils import strip_quotes
from django.db.models import ForeignKey


class DatabaseSchemaEditor(PostgresDatabaseSchemaEditor):
    # The PostgreSQL backend uses "SET CONSTRAINTS ... IMMEDIATE" before
    # "ALTER TABLE..." to run any any deferred checks to allow dropping the
    # foreign key in the same transaction. This doesn't apply to cockroachdb.
    sql_delete_fk = "ALTER TABLE %(table)s DROP CONSTRAINT %(name)s"

    # "ALTER TABLE ... DROP CONSTRAINT ..." not supported for dropping UNIQUE
    # constraints; must use this instead.
    sql_delete_unique = "DROP INDEX %(name)s CASCADE"

    # The PostgreSQL backend uses "SET CONSTRAINTS ... IMMEDIATE" after
    # creating this foreign key. This isn't supported by CockroachDB.
    sql_create_column_inline_fk = 'CONSTRAINT %(name)s REFERENCES %(to_table)s(%(to_column)s)%(deferrable)s'

    # The PostgreSQL backend uses "SET CONSTRAINTS ... IMMEDIATE" after this
    # statement. This isn't supported by CockroachDB.
    sql_update_with_default = "UPDATE %(table)s SET %(column)s = %(default)s WHERE %(column)s IS NULL"

    def __enter__(self):
        super().__enter__()
        # As long as DatabaseFeatures.can_rollback_ddl = False, compose() may
        # fail if connection is None as per
        # https://github.com/django/django/pull/15687#discussion_r1038175823.
        # See also https://github.com/django/django/pull/15687#discussion_r1041503991.
        self.connection.ensure_connection()
        return self

    def add_index(self, model, index, concurrently=False):
        if index.contains_expressions and not self.connection.features.supports_expression_indexes:
            return None
        super().add_index(model, index, concurrently)

    def remove_index(self, model, index, concurrently=False):
        if index.contains_expressions and not self.connection.features.supports_expression_indexes:
            return None
        super().remove_index(model, index, concurrently)

    def _index_columns(self, table, columns, col_suffixes, opclasses):
        # cockroachdb doesn't support PostgreSQL opclasses.
        return BaseDatabaseSchemaEditor._index_columns(self, table, columns, col_suffixes, opclasses)

    def _create_like_index_sql(self, model, field):
        # cockroachdb doesn't support LIKE indexes.
        return None

    def _alter_field(self, model, old_field, new_field, old_type, new_type,
                     old_db_params, new_db_params, strict=False):
        # ALTER COLUMN TYPE is experimental.
        # https://github.com/cockroachdb/cockroach/issues/49329
        if (
            not self.connection.features.is_cockroachdb_25_1 and (
                old_type != new_type or
                getattr(old_field, 'db_collation', None) != getattr(new_field, 'db_collation', None)
            )
        ):
            self.execute('SET enable_experimental_alter_column_type_general = true')
        # Skip to the base class to avoid trying to add or drop
        # PostgreSQL-specific LIKE indexes.
        BaseDatabaseSchemaEditor._alter_field(
            self, model, old_field, new_field, old_type, new_type, old_db_params,
            new_db_params, strict,
        )
        # Add or remove `DEFAULT unique_rowid()` for AutoField.
        old_suffix = old_field.db_type_suffix(self.connection)
        new_suffix = new_field.db_type_suffix(self.connection)
        if old_suffix != new_suffix:
            if new_suffix:
                self.execute(self.sql_alter_column % {
                    'table': self.quote_name(model._meta.db_table),
                    'changes': 'ALTER COLUMN %(column)s SET %(expression)s' % {
                        'column': self.quote_name(new_field.column),
                        'expression': new_suffix,
                    }
                })
            else:
                self.execute(self.sql_alter_column % {
                    'table': self.quote_name(model._meta.db_table),
                    'changes': 'ALTER COLUMN %(column)s DROP DEFAULT' % {
                        'column': self.quote_name(new_field.column),
                    }
                })

    def _alter_column_type_sql(self, model, old_field, new_field, new_type, old_collation, new_collation):
        new_internal_type = new_field.get_internal_type()
        old_internal_type = old_field.get_internal_type()
        # Make ALTER TYPE with AutoField make sense.
        auto_field_types = {'AutoField', 'BigAutoField', 'SmallAutoField'}
        old_is_auto = old_internal_type in auto_field_types
        new_is_auto = new_internal_type in auto_field_types
        if new_is_auto and not old_is_auto:
            column = strip_quotes(new_field.column)
            return (
                (
                    self.sql_alter_column_type % {
                        "column": self.quote_name(column),
                        "type": new_type,
                        "collation": "",
                    },
                    [],
                ),
                # The PostgreSQL backend manages the column's identity here but
                # this isn't applicable on CockroachDB because unique_rowid()
                # is used instead.
                [],
            )
        else:
            return BaseDatabaseSchemaEditor._alter_column_type_sql(
                self, model, old_field, new_field, new_type,
                old_collation, new_collation,
            )

    def _field_should_be_indexed(self, model, field):
        # Foreign keys are automatically indexed by cockroachdb.
        return not isinstance(field, ForeignKey) and super()._field_should_be_indexed(model, field)
