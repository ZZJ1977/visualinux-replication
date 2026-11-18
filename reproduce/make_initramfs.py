"""Package the classroom workload and a serial console into a small Linux initramfs."""

import argparse
import gzip
import io
import stat
from pathlib import Path


def make_initramfs(workload):
    if workload[:6] != b"\x7fELF\x02\x01" or workload[18:20] != b"\x3e\x00":
        raise ValueError("Compile workload.c as an x86-64 Linux ELF first.")
    entries = [
        ("dev", stat.S_IFDIR | 0o755, b"", 0, 0),
        ("dev/console", stat.S_IFCHR | 0o600, b"", 5, 1),
        ("bin", stat.S_IFDIR | 0o755, b"", 0, 0),
        ("bin/vl-demo", stat.S_IFREG | 0o755, workload, 0, 0),
        ("TRAILER!!!", 0, b"", 0, 0),
    ]
    data = io.BytesIO()
    for inode, (name, mode, payload, major, minor) in enumerate(entries, start=1):
        encoded_name = name.encode("ascii") + b"\0"
        fields = (inode, mode, 0, 0, 1, 0, len(payload), 0, 0,
                  major, minor, len(encoded_name), 0)
        header = "070701" + "".join(f"{value:08x}" for value in fields)
        data.write(header.encode("ascii") + encoded_name)
        data.write(b"\0" * (-data.tell() % 4))
        data.write(payload)
        data.write(b"\0" * (-data.tell() % 4))
    return gzip.compress(data.getvalue(), mtime=0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("elf", type=Path, help="workload compiled as a static x86-64 Linux ELF")
    parser.add_argument("output", type=Path, help="output .cpio.gz file")
    args = parser.parse_args()
    args.output.write_bytes(make_initramfs(args.elf.read_bytes()))
