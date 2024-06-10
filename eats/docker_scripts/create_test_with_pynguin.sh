echo "Running Pynguin on module $module_name"
pynguin \
    --project-path $PROJECT_ROOT \
    --output-path /workplace/pynguin-results \
    --module-name $module_name \
    --maximum-search-time $maximum_search_time \
    --maximum-iterations $maximum_iterations \
    -v
