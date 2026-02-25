import h5py

filename = "test.h5"

with h5py.File(filename, "w") as file:
    file.require_group("fensap/drop")
    file.require_group("fensap/drop")

