from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from django.db.backends.postgresql.schema import (
    DatabaseSchemaEditor as PostgresDatabaseSchemaEditor,
)
from django.db.models import ForeignKey


class DatabaseSchemaEditor(PostgresDatabaseSchemaEditor):
    # Don't include the USING clause as per
    # https://github.com/cockroachdb/cockroach/issues/49329#issuecomment-666585887
    sql_alter_column_type = "ALTER COLUMN %(column)s TYPE %(type)s"

    @property
    def sql_create_index(self):
        if self.connection.features.is_cockroachdb_20_2:
            return PostgresDatabaseSchemaEditor.sql_create_index
        else:
            return 'CREATE INDEX %(name)s ON %(table)s%(using)s (%(columns)s)%(extra)s'

    # The PostgreSQL backend uses "SET CONSTRAINTS ... IMMEDIATE" before
    # "ALTER TABLE..." to run any any deferred checks to allow dropping the
    # foreign key in the same transaction. This doesn't apply to cockroachdb.
    sql_delete_fk = "ALTER TABLE %(table)s DROP CONSTRAINT %(name)s"

    # "ALTER TABLE ... DROP CONSTRAINT ..." not supported for dropping UNIQUE
    # constraints; must use this instead.
    sql_delete_unique = "DROP INDEX %(name)s CASCADE"

    def _index_columns(self, table, columns, col_suffixes, opclasses):
        # cockroachdb doesn't support PostgreSQL opclasses.
        return BaseDatabaseSchemaEditor._index_columns(self, table, columns, col_suffixes, opclasses)

    def _create_like_index_sql(self, model, field):
        # cockroachdb doesn't support LIKE indexes.
        return None

    def _alter_field(self, model, old_field, new_field, old_type, new_type,
                     old_db_params, new_db_params, strict=False):
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

    def _alter_column_type_sql(self, model, old_field, new_field, new_type):
        if new_type.lower() in ("serial", "bigserial"):
            column = new_field.column
            col_type = "integer" if new_type.lower() == "serial" else "bigint"
            return (
                (
                    self.sql_alter_column_type % {
                        "column": self.quote_name(column),
                        "type": col_type,
                    },
                    [],
                ),
                # The PostgreSQL backend manages the column sequence here but
                # this isn't applicable on CockroachDB because unique_rowid()
                # is used instead of sequences.
                [],
            )
        else:
            return BaseDatabaseSchemaEditor._alter_column_type_sql(self, model, old_field, new_field, new_type)

    def _field_should_be_indexed(self, model, field):
        # Foreign keys are automatically indexed by cockroachdb.
        return not isinstance(field, ForeignKey) and super()._field_should_be_indexed(model, field)
