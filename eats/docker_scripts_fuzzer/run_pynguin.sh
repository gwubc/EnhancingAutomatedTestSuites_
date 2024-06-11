echo "Running Pynguin on module $module_name"
pynguin \
    --project-path $PROJECT_ROOT \
    --output-path /workplace/finial_pynguin_results \
    --module-name $module_name \
    --maximum-search-time 300 \
    --maximum-iterations 300 \
    --initial-population-seeding 1 \
    --initial-population-data /workplace/recreation_results \
    --seed 1 \
    -v

python /usr/src/scripts_fuzzer/rename.py