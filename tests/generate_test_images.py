"""
Génère deux images disque de test (raw) pour valider un parser MBR / GPT
écrit par ailleurs. Ce script sert uniquement à fabriquer des fixtures de
test réalistes -- il ne fait pas le travail de parsing.
"""
import struct
import uuid
import zlib
import json

SECTOR = 512


def guid_to_mixed_endian_bytes(guid_str: str) -> bytes:
    """Les GUID GPT sont stockés en 'mixed-endian' : les 3 premiers champs
    sont little-endian, les 2 derniers restent en ordre big-endian (réseau)."""
    u = uuid.UUID(guid_str)
    be = u.bytes  # 16 octets, RFC4122 big-endian
    return be[0:4][::-1] + be[4:6][::-1] + be[6:8][::-1] + be[8:16]


# ---------------------------------------------------------------------------
# 1) Image MBR pure
# ---------------------------------------------------------------------------
def build_mbr_image(path, total_sectors=10240):  # 5 MiB
    data = bytearray(total_sectors * SECTOR)

    bootstrap = b"\x00" * 446
    entries = bytearray()

    def make_entry(status, ptype, lba_start, sectors):
        chs_dummy = b"\x00\x00\x00"
        return struct.pack(
            "<B3sB3sII",
            status, chs_dummy, ptype, chs_dummy, lba_start, sectors
        )

    entries += make_entry(0x80, 0x07, 2048, 4096)   # NTFS, bootable
    entries += make_entry(0x00, 0x83, 6144, 4096)   # Linux
    entries += make_entry(0x00, 0x00, 0, 0)         # vide
    entries += make_entry(0x00, 0x00, 0, 0)         # vide

    mbr = bootstrap + entries + b"\x55\xaa"
    assert len(mbr) == 512
    data[0:512] = mbr

    with open(path, "wb") as f:
        f.write(data)

    return {
        "type": "MBR",
        "sector_size": SECTOR,
        "total_sectors": total_sectors,
        "signature_offset": 510,
        "signature_expected": "55AA",
        "partitions": [
            {"index": 1, "bootable": True, "type_hex": "0x07", "type_name": "NTFS/exFAT",
             "lba_start": 2048, "sectors": 4096},
            {"index": 2, "bootable": False, "type_hex": "0x83", "type_name": "Linux",
             "lba_start": 6144, "sectors": 4096},
            {"index": 3, "bootable": False, "type_hex": "0x00", "type_name": "vide/non utilisée",
             "lba_start": 0, "sectors": 0},
            {"index": 4, "bootable": False, "type_hex": "0x00", "type_name": "vide/non utilisée",
             "lba_start": 0, "sectors": 0},
        ],
    }


# ---------------------------------------------------------------------------
# 2) Image GPT (avec MBR protecteur + table primaire + table de secours)
# ---------------------------------------------------------------------------
def build_gpt_image(path, total_sectors=40960):  # 20 MiB
    data = bytearray(total_sectors * SECTOR)
    last_lba = total_sectors - 1

    num_entries = 128
    entry_size = 128
    table_sectors = (num_entries * entry_size) // SECTOR  # 32 secteurs

    primary_table_lba = 2
    primary_header_lba = 1
    backup_table_lba = last_lba - table_sectors  # dernier secteur de table avant le header de secours
    backup_header_lba = last_lba

    first_usable_lba = primary_table_lba + table_sectors  # 34
    last_usable_lba = backup_table_lba - 1

    disk_guid = str(uuid.uuid4())

    # --- protective MBR (secteur 0) ---
    chs_dummy_start = b"\x00\x02\x00"
    chs_dummy_end = b"\xff\xff\xff"
    prot_size = min(last_lba, 0xFFFFFFFF)
    entry = struct.pack(
        "<B3sB3sII",
        0x00, chs_dummy_start, 0xEE, chs_dummy_end, 1, prot_size
    )
    mbr = b"\x00" * 446 + entry + b"\x00" * (16 * 3) + b"\x55\xaa"
    data[0:512] = mbr

    # --- partitions ---
    esp_type = "C12A7328-F81F-11D2-BA4B-00A0C93EC93B"       # EFI System Partition
    data_type = "EBD0A0A2-B9E5-4433-87C0-68B6B72699C7"      # Microsoft Basic Data

    esp_guid = str(uuid.uuid4())
    data_guid = str(uuid.uuid4())

    part1 = {
        "type_guid": esp_type, "unique_guid": esp_guid,
        "first_lba": 2048, "last_lba": 6143,
        "attrs": 0, "name": "EFI System",
    }
    part2 = {
        "type_guid": data_type, "unique_guid": data_guid,
        "first_lba": 6144, "last_lba": last_usable_lba,
        "attrs": 0, "name": "DATA",
    }

    def pack_entry(p):
        name_utf16 = p["name"].encode("utf-16-le")
        name_utf16 = name_utf16 + b"\x00" * (72 - len(name_utf16))
        return (
            guid_to_mixed_endian_bytes(p["type_guid"]) +
            guid_to_mixed_endian_bytes(p["unique_guid"]) +
            struct.pack("<QQQ", p["first_lba"], p["last_lba"], p["attrs"]) +
            name_utf16
        )

    table = bytearray(num_entries * entry_size)
    table[0:entry_size] = pack_entry(part1)
    table[entry_size:entry_size * 2] = pack_entry(part2)

    table_crc = zlib.crc32(bytes(table)) & 0xFFFFFFFF

    def pack_header(current_lba, backup_lba, part_table_lba):
        header = struct.pack(
            "<8sIIIIQQQQ16sQII",
            b"EFI PART",
            0x00010000,      # revision 1.0
            92,               # header size
            0,                # CRC32 placeholder (calculé après)
            0,                # reserved
            current_lba,
            backup_lba,
            first_usable_lba,
            last_usable_lba,
            guid_to_mixed_endian_bytes(disk_guid),
            part_table_lba,
            num_entries,
            entry_size,
        )
        # le CRC32 des entrées est stocké après (uint32), struct ci-dessus ne le contient pas encore
        header += struct.pack("<I", table_crc)
        header = header[:92]  # doit faire exactement 92 octets
        # recalcul du CRC32 du header lui-même, champ CRC (offset 16, 4 octets) mis à 0 pendant le calcul
        header_for_crc = header[:16] + b"\x00\x00\x00\x00" + header[20:]
        header_crc = zlib.crc32(header_for_crc) & 0xFFFFFFFF
        header = header[:16] + struct.pack("<I", header_crc) + header[20:]
        sector = header + b"\x00" * (SECTOR - len(header))
        return sector

    primary_header = pack_header(primary_header_lba, backup_header_lba, primary_table_lba)
    backup_header = pack_header(backup_header_lba, primary_header_lba, backup_table_lba)

    data[primary_header_lba * SECTOR: primary_header_lba * SECTOR + SECTOR] = primary_header
    data[primary_table_lba * SECTOR: primary_table_lba * SECTOR + len(table)] = table

    data[backup_table_lba * SECTOR: backup_table_lba * SECTOR + len(table)] = table
    data[backup_header_lba * SECTOR: backup_header_lba * SECTOR + SECTOR] = backup_header

    with open(path, "wb") as f:
        f.write(data)

    return {
        "type": "GPT",
        "sector_size": SECTOR,
        "total_sectors": total_sectors,
        "last_lba": last_lba,
        "protective_mbr": {
            "signature_offset": 510, "signature_expected": "55AA",
            "partition_type_hex": "0xEE",
        },
        "primary_header_lba": primary_header_lba,
        "backup_header_lba": backup_header_lba,
        "primary_table_lba": primary_table_lba,
        "backup_table_lba": backup_table_lba,
        "num_partition_entries": num_entries,
        "size_of_partition_entry": entry_size,
        "first_usable_lba": first_usable_lba,
        "last_usable_lba": last_usable_lba,
        "disk_guid": disk_guid,
        "header_crc32_note": "calculé sur les 92 premiers octets du header, champ CRC32 (offset 16) mis à 0 pendant le calcul",
        "partition_array_crc32": hex(table_crc),
        "partitions": [
            {**part1, "type_name": "EFI System Partition"},
            {**part2, "type_name": "Microsoft Basic Data"},
        ],
    }


if __name__ == "__main__":
    mbr_info = build_mbr_image("fixtures/test_mbr.img")
    gpt_info = build_gpt_image("fixtures/test_gpt.img")

    with open("fixtures/answer_key.json", "w") as f:
        json.dump({"test_mbr.img": mbr_info, "test_gpt.img": gpt_info}, f, indent=2)

    print("OK: fixtures/test_mbr.img, fixtures/test_gpt.img, fixtures/answer_key.json générés")
