class _Threading:
    def set_intra_op_parallelism_threads(self, num_threads: int) -> None: ...
    def set_inter_op_parallelism_threads(self, num_threads: int) -> None: ...

class _Config:
    threading: _Threading

config: _Config
