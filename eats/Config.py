import typing


class Config:
    TARGET_PROGRAM_ROOT: str
    MAX_WORKERS: int

    working_dir: str
    module_names: typing.List[str]

    max_pynguin_search_time_first_search: int
    max_pynguin_iterations_first_search: int

    max_pynguin_search_time_second_search: int
    max_pynguin_iterations_second_search: int

    max_mutmut_time: int

    max_fuzz_time: int
    max_fuzz_iterations: int
