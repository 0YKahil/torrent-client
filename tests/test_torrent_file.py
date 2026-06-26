from torrent_client.torrent_file import TorrentFile


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
