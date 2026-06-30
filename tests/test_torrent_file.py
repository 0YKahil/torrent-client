import hashlib

import pytest

from torrent_client import bencode
from torrent_client.torrent_file import TorrentFile


@pytest.fixture
def valid_torrent():
    torrent = TorrentFile.__new__(TorrentFile)
    torrent.path = "example.torrent"
    torrent.raw_bytes = b"torrent data"
    torrent.name = b"example.txt"
    torrent.announce = b"https://tracker.example/announce"
    torrent.piece_length = 4
    torrent.length = 10
    torrent.pieces = b"a" * 60
    torrent.info = {
        b"name": torrent.name,
        b"piece length": torrent.piece_length,
        b"length": torrent.length,
        b"pieces": torrent.pieces,
    }
    torrent.data = {b"announce": torrent.announce, b"info": torrent.info}
    return torrent


def test_piece_count_counts_twenty_byte_hashes():
    torrent = TorrentFile.__new__(TorrentFile)
    torrent.pieces = b"a" * 60

    assert torrent.piece_count() == 3


def test_piece_hashes_splits_pieces_into_twenty_byte_hashes():
    torrent = TorrentFile.__new__(TorrentFile)
    first_hash = b"a" * 20
    second_hash = b"b" * 20
    third_hash = b"c" * 20
    torrent.pieces = first_hash + second_hash + third_hash

    assert torrent.piece_hashes() == [first_hash, second_hash, third_hash]


def test_piece_hash_returns_hash_for_piece_index():
    torrent = TorrentFile.__new__(TorrentFile)
    first_hash = b"a" * 20
    second_hash = b"b" * 20
    torrent.pieces = first_hash + second_hash

    assert torrent.piece_hash(1) == second_hash


@pytest.mark.parametrize("index", [-1, 2])
def test_piece_hash_rejects_invalid_index(index):
    torrent = TorrentFile.__new__(TorrentFile)
    torrent.pieces = b"a" * 40

    with pytest.raises(IndexError):
        torrent.piece_hash(index)


def test_piece_offset_for_first_piece_is_zero():
    torrent = TorrentFile.__new__(TorrentFile)
    torrent.pieces = b"a" * 80
    torrent.piece_length = 256

    assert torrent.piece_offset(0) == 0


def test_piece_offset_for_later_piece_uses_piece_length():
    torrent = TorrentFile.__new__(TorrentFile)
    torrent.pieces = b"a" * 80
    torrent.piece_length = 256

    assert torrent.piece_offset(2) == 512


def test_piece_size_for_normal_piece_is_piece_length():
    torrent = TorrentFile.__new__(TorrentFile)
    torrent.pieces = b"a" * 80
    torrent.piece_length = 256
    torrent.length = 1000

    assert torrent.piece_size(1) == 256


def test_piece_size_for_final_piece_is_remaining_bytes():
    torrent = TorrentFile.__new__(TorrentFile)
    torrent.pieces = b"a" * 80
    torrent.piece_length = 256
    torrent.length = 1000

    assert torrent.piece_size(3) == 232


@pytest.mark.parametrize("index", [-1, 4])
def test_piece_offset_rejects_invalid_index(index):
    torrent = TorrentFile.__new__(TorrentFile)
    torrent.pieces = b"a" * 80
    torrent.piece_length = 256

    with pytest.raises(IndexError):
        torrent.piece_offset(index)


@pytest.mark.parametrize("index", [-1, 4])
def test_piece_size_rejects_invalid_index(index):
    torrent = TorrentFile.__new__(TorrentFile)
    torrent.pieces = b"a" * 80
    torrent.piece_length = 256
    torrent.length = 1000

    with pytest.raises(IndexError):
        torrent.piece_size(index)


def test_verify_piece_accepts_data_matching_piece_hash():
    piece_data = b"hello torrent"
    torrent = TorrentFile.__new__(TorrentFile)
    torrent.pieces = hashlib.sha1(piece_data).digest()
    torrent.piece_length = len(piece_data)
    torrent.length = len(piece_data)

    assert torrent.verify_piece(0, piece_data) is True


def test_verify_piece_rejects_data_not_matching_piece_hash():
    expected_data = b"hello torrent"
    torrent = TorrentFile.__new__(TorrentFile)
    torrent.pieces = hashlib.sha1(expected_data).digest()
    torrent.piece_length = len(expected_data)
    torrent.length = len(expected_data)

    assert torrent.verify_piece(0, b"jello torrent") is False


def test_verify_piece_rejects_data_with_wrong_size():
    expected_data = b"hello torrent"
    torrent = TorrentFile.__new__(TorrentFile)
    torrent.pieces = hashlib.sha1(expected_data).digest()
    torrent.piece_length = len(expected_data)
    torrent.length = len(expected_data)

    assert torrent.verify_piece(0, expected_data[:-1]) is False


@pytest.mark.parametrize("index", [-1, 1])
def test_verify_piece_rejects_invalid_index(index):
    torrent = TorrentFile.__new__(TorrentFile)
    torrent.pieces = hashlib.sha1(b"data").digest()
    torrent.piece_length = 4
    torrent.length = 4

    with pytest.raises(IndexError):
        torrent.verify_piece(index, b"data")


def test_validate_accepts_consistent_single_file_metadata(valid_torrent):
    assert valid_torrent.validate() is None


@pytest.mark.parametrize("piece_length", [0, -1, "4"])
def test_validate_rejects_invalid_piece_length(valid_torrent, piece_length):
    valid_torrent.piece_length = piece_length

    with pytest.raises(ValueError):
        valid_torrent.validate()


@pytest.mark.parametrize("length", [-1, "10"])
def test_validate_rejects_invalid_file_length(valid_torrent, length):
    valid_torrent.length = length

    with pytest.raises(ValueError):
        valid_torrent.validate()


def test_validate_rejects_piece_hash_blob_not_divisible_by_twenty(valid_torrent):
    valid_torrent.pieces = b"a" * 21

    with pytest.raises(ValueError):
        valid_torrent.validate()


def test_validate_rejects_wrong_number_of_piece_hashes(valid_torrent):
    valid_torrent.pieces = b"a" * 40

    with pytest.raises(ValueError):
        valid_torrent.validate()


def test_from_file_reads_decodes_and_validates_torrent(tmp_path, monkeypatch):
    path = tmp_path / "example.torrent"
    raw_bytes = b"encoded torrent"
    path.write_bytes(raw_bytes)
    data = {
        b"announce": b"https://tracker.example/announce",
        b"info": {
            b"name": b"example.txt",
            b"piece length": 4,
            b"length": 4,
            b"pieces": b"a" * 20,
        },
    }
    monkeypatch.setattr(bencode, "decode", lambda value: data, raising=False)

    torrent = TorrentFile.from_file(path)

    assert torrent.path == path
    assert torrent.raw_bytes == raw_bytes
    assert torrent.data == data


def test_info_hash_is_sha1_of_bencoded_info(valid_torrent, monkeypatch):
    encoded_info = b"encoded info dictionary"
    encoded_values = []

    def fake_encode(value):
        encoded_values.append(value)
        return encoded_info

    monkeypatch.setattr(bencode, "encode", fake_encode, raising=False)

    assert valid_torrent.info_hash() == hashlib.sha1(encoded_info).digest()
    assert encoded_values == [valid_torrent.info]


def test_info_hash_hex_returns_readable_hexadecimal_hash(valid_torrent, monkeypatch):
    encoded_info = b"encoded info dictionary"
    monkeypatch.setattr(bencode, "encode", lambda value: encoded_info, raising=False)

    assert valid_torrent.info_hash_hex() == hashlib.sha1(encoded_info).hexdigest()


def test_tracker_urls_includes_announce_and_flattens_announce_list(valid_torrent):
    valid_torrent.data[b"announce-list"] = [
        [b"https://tracker.example/announce"],
        [b"https://backup.example/announce", b"https://third.example/announce"],
    ]

    assert valid_torrent.tracker_urls() == [
        "https://tracker.example/announce",
        "https://backup.example/announce",
        "https://third.example/announce",
    ]


def test_tracker_urls_uses_announce_when_no_announce_list(valid_torrent):
    assert valid_torrent.tracker_urls() == ["https://tracker.example/announce"]


def test_name_text_decodes_utf8_name(valid_torrent):
    valid_torrent.name = "caf\u00e9.txt".encode()

    assert valid_torrent.name_text() == "caf\u00e9.txt"
