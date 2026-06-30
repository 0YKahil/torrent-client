"""
TorrentFile Class

Operations for opening and inspecting .torrent files
"""

import math
import hashlib

from torrent_client import bencode


class TorrentFile:
    def __init__(self, path, raw_bytes, data):
        self.path = path
        self.raw_bytes = raw_bytes
        self.data = data
        
        self.announce = data[b"announce"] # URL of tracker
        self.info = data[b"info"] # Dict: contains fields below 

        self.name = self.info[b"name"]
        self.piece_length = self.info[b"piece length"] # maps to number of bytes in each piece the file is split into
        self.pieces = self.info[b"pieces"] # maps to string with length multiple of 2. Subdivided into strings of lenght 20 -> SHA1 hash of the piece at corresponding idx
        self.length = self.info[b"length"] # length of file in bytes
        
        
    def piece_count(self):
        pieces_length = len(self.pieces)
        if (pieces_length % 20 != 0):
            raise Exception('Pieces is not multiple of 20 length') 
        
        return len(self.pieces) // 20
    
    
    def piece_hashes(self):
        hashes = []
        num_pieces = self.piece_count()
        pieces = self.pieces
        
        for i in range(0, num_pieces * 20, 20):
            # slice the next 20 in pieces into hashes
            hashes.append(pieces[i:(i+20)])
            
        return hashes
    
    
    def piece_hash(self, index):
        self.verify_index(index)
        return self.piece_hashes()[index]
    
    
    def piece_offset(self, index):
        self.verify_index(index)
        return index * self.piece_length
    
    
    def piece_size(self, index):
        self.verify_index(index)
        if index == self.piece_count() - 1:
            return self.length - self.piece_offset(index)
        else:
            return self.piece_length


    def verify_piece(self, index, piece_data):
        self.verify_index(index)
        if len(piece_data) != self.piece_size(index):
            return False
        
        piece_hash = self.piece_hash(index)
        computed_hash = hashlib.sha1(piece_data).digest()
        return piece_hash == computed_hash
    
    
    def validate(self):
        if len(self.pieces) % 20 != 0:
            raise ValueError('Pieces field length is not a multiple of 20')
        
        if not isinstance(self.length, int) or self.length < 0:
            raise ValueError('File length must be a non-negative integer')
        
        if not isinstance(self.piece_length, int) or self.piece_length <= 0:
            raise ValueError('Piece length must be a positive integer')
        
        if math.ceil(self.length / self.piece_length) != self.piece_count():
            raise ValueError('Inconsistent piece count')
        
        
    @classmethod
    def from_file(cls, path):
        with open(path, 'rb') as f:
            raw_bytes = f.read()
        
        data = bencode.decode(raw_bytes)
        torrent = cls(path, raw_bytes, data)
        torrent.validate()
        return torrent
    
    
    def info_hash(self):
        info_bytes = bencode.encode(self.info)
        return hashlib.sha1(info_bytes).digest()
    
    
    def info_hash_hex(self):
        return self.info_hash().hex()
    
    
    def tracker_urls(self):
        trackers = [self.data[b'announce']]
        for tier in self.data.get(b'announce-list', []):
            trackers.extend(tier)

        urls = []
        for tracker in trackers:
            url = tracker.decode('utf-8') if isinstance(tracker, bytes) else tracker
            if url not in urls:
                urls.append(url)
        return urls
    
    
    def name_text(self):
        return self.name.decode('utf-8')
    
        
    # helpers
    def verify_index(self, index):
        if (index < 0 or index >= self.piece_count()):
            raise IndexError('Index out of bounds')
