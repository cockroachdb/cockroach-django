from django.contrib.gis.db.backends.postgis.features import (
    DatabaseFeatures as PostGISFeatures,
)
from django.db.backends.postgresql.psycopg_any import is_psycopg3
from django.utils.functional import cached_property

from django_cockroachdb.features import DatabaseFeatures as CockroachFeatures


class DatabaseFeatures(CockroachFeatures, PostGISFeatures):
    supports_raster = False
    # Not supported: https://github.com/cockroachdb/cockroach/issues/57092
    supports_left_right_lookups = False
    # unimplemented: column point is of type geometry and thus is not indexable
    # https://go.crdb.dev/issue/35730
    supports_geometry_field_unique_index = False

    @cached_property
    def django_test_expected_failures(self):
        expected_failures = super().django_test_expected_failures
        expected_failures.update({
            # ST_AsText output different from PostGIS (extra space):
            # https://github.com/cockroachdb/cockroach/issues/53651
            'gis_tests.geoapp.test_functions.GISFunctionsTests.test_aswkt',
            # Unsupported ~= (same_as/exact) operator:
            # https://github.com/cockroachdb/cockroach/issues/57096
            'gis_tests.geoapp.tests.GeoLookupTest.test_equals_lookups',
            'gis_tests.geoapp.tests.GeoLookupTest.test_null_geometries_excluded_in_lookups',
            'gis_tests.gis_migrations.test_operations.OperationTests.test_add_check_constraint',
            'gis_tests.relatedapp.tests.RelatedGeoModelTest.test06_f_expressions',
            # unknown signature: st_union(geometry, geometry)
            # https://github.com/cockroachdb/cockroach/issues/49064
            'gis_tests.distapp.tests.DistanceTest.test_dwithin',
            'gis_tests.geoapp.test_functions.GISFunctionsTests.test_diff_intersection_union',
            'gis_tests.geoapp.test_functions.GISFunctionsTests.test_union_mixed_srid',
            'gis_tests.geoapp.test_functions.GISFunctionsTests.test_union',
            'gis_tests.geoapp.tests.GeoLookupTest.test_gis_lookups_with_complex_expressions',
            'gis_tests.geoapp.tests.GeoLookupTest.test_relate_lookup',
            # NotSupportedError: this box2d comparison operator is experimental
            'gis_tests.geoapp.tests.GeoLookupTest.test_contains_contained_lookups',
            # unknown signature: st_distancespheroid(geometry, geometry, string)
            # https://github.com/cockroachdb/cockroach/issues/48922#issuecomment-693096502
            'gis_tests.distapp.tests.DistanceTest.test_distance_lookups_with_expression_rhs',
            'gis_tests.distapp.tests.DistanceTest.test_geodetic_distance_lookups',
            'gis_tests.distapp.tests.DistanceFunctionsTests.test_distance_geodetic_spheroid',
            # st_lengthspheroid(): unimplemented:
            # https://github.com/cockroachdb/cockroach/issues/48968
            'gis_tests.distapp.tests.DistanceFunctionsTests.test_length',
            # Unsupported ~= (https://github.com/cockroachdb/cockroach/issues/57096)
            # and @ operators (https://github.com/cockroachdb/cockroach/issues/56124).
            'gis_tests.geogapp.tests.GeographyTest.test_operators_functions_unavailable_for_geography',
            # unknown function: st_3dperimeter
            # https://github.com/cockroachdb/cockroach/issues/60871
            'gis_tests.geo3d.tests.Geo3DFunctionsTests.test_perimeter',
            # unknown function: st_3dextent()
            # https://github.com/cockroachdb/cockroach/issues/60864
            'gis_tests.geo3d.tests.Geo3DTest.test_extent',
            'gis_tests.geo3d.tests.Geo3DTest.test_extent3d_filter',
            # unknown signature: st_scale(geometry, decimal, decimal, decimal)
            # https://github.com/cockroachdb/cockroach/issues/49027
            'gis_tests.geo3d.tests.Geo3DFunctionsTests.test_scale',
            # ASKML not supported:
            # https://github.com/cockroachdb/cockroach/issues/48881
            'gis_tests.geo3d.tests.Geo3DFunctionsTests.test_kml',
            # st_lengthspheroid(): unimplemented:
            # https://github.com/cockroachdb/cockroach/issues/48968
            'gis_tests.geo3d.tests.Geo3DFunctionsTests.test_length',
            # unimplemented: ALTER COLUMN TYPE requiring rewrite of on-disk
            # data is currently not supported for columns that are part of an
            # index: https://github.com/cockroachdb/cockroach/issues/47636
            'gis_tests.gis_migrations.test_operations.OperationTests.test_alter_geom_field_dim',
            'gis_tests.gis_migrations.test_operations.OperationTests.test_alter_field_with_spatial_index',
            # 3D opclass not present on CockroachDB:
            # https://github.com/cockroachdb/cockroach/issues/47420#issuecomment-969578772
            'gis_tests.gis_migrations.test_operations.OperationTests.test_add_3d_field_opclass',
        })
        if is_psycopg3 and not self.is_cockroachdb_24_1:
            expected_failures.update({
                # QuerySet.bulk_create() doesn't work with geometries after
                # https://github.com/django/django/commit/a16eedcf9c69d8a11d94cac1811018c5b996d491
                # could not parse geometry: error parsing EWKB hex: encoding/hex:
                # invalid byte: U+003A ':'
                # https://github.com/cockroachdb/cockroach/issues/138140
                'gis_tests.geoapp.test_functions.GISFunctionsTests.test_area_lookups',
            })
        if self.uses_server_side_binding:
            expected_failures.update({
                # unknown signature: st_scale(geometry, int, int)
                'gis_tests.geoapp.test_functions.GISFunctionsTests.test_scale',
            })
        else:
            expected_failures.update({
                # unknown signature: st_dwithin(geography, geometry, decimal) (desired <bool>)
                # https://github.com/cockroachdb/cockroach/issues/53720
                'gis_tests.geogapp.tests.GeographyTest.test02_distance_lookup',
            })
        return expected_failures
