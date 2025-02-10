import datetime

from django.db.models import (
    DateTimeField, DecimalField, FloatField, IntegerField,
)
from django.db.models.expressions import When
from django.db.models.functions import (
    ACos, ASin, ATan, ATan2, Cast, Ceil, Coalesce, Collate, Cos, Cot, Degrees,
    Exp, Floor, JSONArray, JSONObject, Ln, Log, Radians, Round, Sin, Sqrt,
    StrIndex, Tan,
)


def coalesce(self, compiler, connection, **extra_context):
    # When coalescing a timestamptz column and a Python datetime, the datetime
    # must be cast to timestamptz (DateTimeField) to avoid "incompatible
    # COALESCE expressions: expected 'YYYY-MM-DDTHH:MM:SS'::TIMESTAMP to be of
    # type timestamptz, found type timestamp".
    if self.output_field.get_internal_type() == 'DateTimeField':
        clone = self.copy()
        clone.set_source_expressions([
            Cast(expression, DateTimeField()) for expression in self.get_source_expressions()
        ])
        return super(Coalesce, clone).as_sql(compiler, connection, **extra_context)
    return self.as_sql(compiler, connection, **extra_context)


def collate(self, compiler, connection, **extra_context):
    return self.as_sql(
        compiler, connection,
        # CockroachDB requires parentheses around the expression in
        # CREATE INDEX: https://github.com/cockroachdb/cockroach/issues/71240
        template='(%(expressions)s %(function)s %(collation)s)',
        **extra_context
    )


def float_cast(self, compiler, connection, **extra_context):
    # Most cockroachdb math functions require float arguments instead of
    # decimal or integer.
    clone = self.copy()
    clone.set_source_expressions([
        Cast(expression, FloatField()) if isinstance(expression.output_field, (DecimalField, IntegerField))
        else expression for expression in self.get_source_expressions()
    ])
    return clone.as_sql(compiler, connection, **extra_context)


def round_cast(self, compiler, connection, **extra_context):
    # ROUND() doesn't accept integer values. Cast to decimal (rather than
    # float) so that half away from zero rounding is used, consistent with
    # other databases (rather than half to even rounding).
    clone = self.copy()
    value, precision = self.get_source_expressions()
    value = (
        Cast(value, DecimalField(max_digits=2147481649, decimal_places=0))
        if isinstance(value.output_field, IntegerField)
        else value
    )
    clone.set_source_expressions([value, precision])
    return clone.as_sql(compiler, connection, **extra_context)


def when(self, compiler, connection, **extra_context):
    # As for coalesce(), cast datetimes to timestamptz.
    if isinstance(getattr(self.result, 'value', None), datetime.datetime):
        self.result = Cast(self.result, DateTimeField())
    return self.as_sql(compiler, connection, **extra_context)


def register_functions():
    math_funcs_needing_float_cast = (
        ACos, ASin, ATan, ATan2, Ceil, Cos, Cot, Degrees, Exp, Floor, Ln, Log,
        Radians, Sin, Sqrt, Tan,
    )
    for func in math_funcs_needing_float_cast:
        func.as_cockroachdb = float_cast
    Coalesce.as_cockroachdb = coalesce
    Collate.as_cockroachdb = collate
    JSONArray.as_cockroachdb = JSONArray.as_postgresql
    JSONObject.as_cockroachdb = JSONObject.as_postgresql
    Round.as_cockroachdb = round_cast
    StrIndex.as_cockroachdb = StrIndex.as_postgresql
    When.as_cockroachdb = when
