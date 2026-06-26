"""
TorrentFile Class

Operations for opening and inspecting .torrent files
"""

class TorrentFile:
    def __init__(self, path, raw_bytes, data):
        self.path = path
        self.raw_bytes = raw_bytes
        self.data = data
        
        self.announce = data[b"announce"] # URL of tracker
        self.info = data[b"info"] # Dict: contains fields below 

        self.name = self.info[b"name"] # String: suggested name of file
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
        return self.piece_hashes()[index]
    
            