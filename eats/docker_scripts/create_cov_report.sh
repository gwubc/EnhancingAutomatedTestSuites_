export PYTHONPATH="${PYTHONPATH}:${PROJECT_ROOT}"
mv /usr/src/scripts/conftest.py.1 conftest.py
python -m pytest /workplace/tests
rm conftest.py
mv /usr/src/scripts/conftest.py.2 conftest.py
cp /usr/src/scripts/.coveragerc .coveragerc
python -m pytest /workplace/tests --cov=/usr/src/project --cov-branch --cov-report=html:cov_report --cov-report=json:cov_report/coverage.json