# Enhancing Automated Test Suites

### Installation
Clone the repository:\
```git clone https://github.com/gwubc/EnhancingAutomatedTestSuites.git```

Install dependencies:\
```pip install docker```\
or\
```pip install -r requirements.txt```

### Configuration

1. Choose a target project and clone it into the `targets` folder.

2. Edit the `eats.ini` file:
  - change ```TARGET_PROGRAM_ROOT``` to ```./targets/$TargetProject```
  - Update the ```modules_to_test``` parameter as needed.

### Running the Program
Execute the following command:\
```python3 -m eats```

The program will create a folder named `working_dir_#` in the current directory, this can be changed in `eats.ini`.
- Generated tests will be located in the `working_dir_#/tests` folder.
- Coverage and mutation scores can be found under `report#` folders:
  - Report for Pynguin: `report1`
  - Report for Pynguin + Atheris: `report2`

### Benchmark
TODO

