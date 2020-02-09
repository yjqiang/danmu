from enum import IntEnum
from struct import Struct
from typing import Tuple, Iterator


class Header:
    pack_size = 4
    _ = 4
    type_size = 2
    encrypt_size = 1
    other_size = 1

    # header_struct.size == raw_header_size
    header_struct = Struct('<2IH2B')
    raw_header_size = pack_size + _ + type_size + encrypt_size + other_size

    @staticmethod
    def pack(len_pack: int, pack_type: int, encrypt: int, other: int) -> bytes:
        return Header.header_struct.pack(len_pack, len_pack, pack_type, encrypt, other)

    @staticmethod
    def unpack(header: bytes) -> Tuple[int, int, int, int]:
        len_pack, _, pack_type, encrypt, other = Header.header_struct.unpack_from(header)
        if not encrypt and not other:
            return len_pack, pack_type, encrypt, other
        raise ValueError('encrypt != 0 || other != 0')


class Pack:
    @staticmethod
    def pack(str_body: str, pack_type: int, encrypt: int = 0, other: int = 0) -> bytes:
        body = str_body.encode('utf-8')
        end = b'\x00'
        len_pack = Header.raw_header_size + len(body) + len(end) - 4  # 反正减了4，不知道原因
        header = Header.pack(len_pack, pack_type, encrypt, other)
        return header + body + end

    @staticmethod
    def unpack(packs: bytes) -> Iterator[Tuple[int, bytes]]:
        pack_l = 0
        len_packs = len(packs)
        while pack_l != len_packs:
            len_pack, pack_type, _, _ = Header.unpack(packs[pack_l:pack_l+Header.raw_header_size])
            next_pack_l = pack_l + len_pack + 4
            body = packs[pack_l+Header.raw_header_size:next_pack_l - 1]  # 因为最后一个字节是无效0
            yield pack_type, body
            pack_l = next_pack_l


class PackType(IntEnum):
    SEND = 689
    REPLY = 690
