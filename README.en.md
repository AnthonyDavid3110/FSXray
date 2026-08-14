# FSXray

An educational forensic tool to explore, analyze, and interactively visualize the internal structure of filesystems, starting from raw disk images.

## About

FSXray is a learning project in digital forensics. The goal is to understand low-level disk and filesystem structures by parsing them from scratch, byte by byte, rather than relying on existing tools (Autopsy, Sleuth Kit...).

The project starts with parsing partition tables (MBR / GPT) and aims to evolve into supporting multiple filesystems (FAT32, NTFS, ext4...), with an interactive, visual interface for exploring the contents of a disk image.

## Current status

🚧 Actively under development — first building block: MBR and GPT parsing.

## Features

**Available**
- Nothing yet — no parsing code has been written so far

**Planned**
- Master Boot Record (MBR) parsing: partition table, types, start/end sectors
- GUID Partition Table (GPT) parsing: header, partition table, GUIDs, CRC32 validation, primary/backup header comparison
- Filesystem support: FAT32, NTFS, ext4
- Deleted file recovery (carving)
- Interactive, visual interface (directory tree exploration, timeline, disk mapping)
- Analysis report generation

## Installation

```bash
git clone https://github.com/<your-username>/fsxray.git
cd fsxray
pip install -r requirements.txt
```

## Usage

```bash
python fsxray.py path/to/image.img
```

*(to be updated as the implementation progresses)*

## Disclaimer

This project is intended for educational purposes. Use it only on disk images you created yourself (VMs, test files) or within a clear legal framework. Do not use it on third-party hardware without authorization.

## Project structure

```
fsxray/
├── fsxray.py           # entry point (coming soon)
├── partitions/         # MBR / GPT parsers (coming soon)
├── filesystems/        # per-filesystem parsers (coming soon)
├── ui/                  # interactive interface (coming soon)
├── tests/               # test scripts and fixture generation
│   └── fixtures/        # test disk images (.img) + answer_key.json
├── docs/                # reference documentation (MBR/GPT guides...)
└── README.md
```

## License

MIT — see [LICENSE](LICENSE).
