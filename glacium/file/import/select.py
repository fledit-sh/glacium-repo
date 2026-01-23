from pathlib import Path
from indexer import FsIndexer, TypeIndex
from service import ConvergJobs

idx = FsIndexer(Path("."))          # alles in root
reg = TypeIndex()
jobs = ConvergJobs(registry=reg)

# irgendeine converg-datei wählen:
meta = next(m for m in idx.files if m.filetype == ("converg", "drop"))

jobs.fs_convert_to_fs(meta, out_root=Path("./out_fs"))
jobs.fs_to_h5_raw(meta, h5_path=Path("./case.h5"))
jobs.fs_convert_to_h5_converted(meta, h5_path=Path("./case.h5"))
jobs.h5_raw_to_h5_converted(meta, h5_path=Path("./case.h5"))
jobs.h5_raw_to_fs_spawn(meta, h5_path=Path("./case.h5"), out_root=Path("./spawn_raw"))
jobs.h5_converted_to_fs_spawn(meta, h5_path=Path("./case.h5"), out_root=Path("./spawn_converted"))
