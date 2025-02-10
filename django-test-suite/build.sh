#!/usr/bin/env bash
set -x

# This script expects the first argument to be a CockroachDB version like
# "v22.1.18" or "LATEST" to test with the nightly CockroachDB build.
VERSION=$1

# clone django into the repo.
rm -rf _django_repo
git clone --depth 1 --single-branch --branch cockroach-5.2.x https://github.com/timgraham/django _django_repo

# install the django requirements.
cd _django_repo/tests/
pip3 install -e ..
pip3 install -r requirements/py3.txt
if [ "${USE_PSYCOPG2}" == "psycopg2" ]; then
    pip3 install psycopg2
else
    pip3 install -r requirements/postgres.txt
fi
cd ../..

# install the django-cockroachdb backend.
pip3 install .

# download and start cockroach
if [ $VERSION == "LATEST" ]
then
    SPATIAL_LIBS="--spatial-libs=$PWD"
    wget "https://edge-binaries.cockroachdb.com/cockroach/cockroach.linux-gnu-amd64.LATEST" -O cockroach_exec
    wget "https://edge-binaries.cockroachdb.com/cockroach/lib/libgeos.linux-gnu-amd64.so.LATEST" -O libgeos.so
    wget "https://edge-binaries.cockroachdb.com/cockroach/lib/libgeos_c.linux-gnu-amd64.so.LATEST" -O libgeos_c.so
    chmod +x cockroach_exec
else
    SPATIAL_LIBS="--spatial-libs=cockroach-${VERSION}.linux-amd64/lib"
    wget "https://binaries.cockroachdb.com/cockroach-${VERSION}.linux-amd64.tgz"
    tar -xvf cockroach-${VERSION}*
    cp cockroach-${VERSION}*/cockroach cockroach_exec
fi

./cockroach_exec start-single-node --insecure $SPATIAL_LIBS &

cd _django_repo/tests/

# Bring in the settings needed to run the tests with cockroach.
cp ../../django-test-suite/cockroach_settings.py .
cp ../../django-test-suite/cockroach_gis_settings.py .

# Run the tests!
python3 ../../django-test-suite/runtests.py
