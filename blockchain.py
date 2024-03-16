class Blockchain:

    def __init__(self):
        self.blocks = []

    def add(self, b):
        self.blocks.append(b)

    def to_str(self, summarized=True, spaces=0):
        s = "blockchain:\n"
        for i, b in enumerate(self.blocks):
            s += b.to_str(summarized, spaces)
        return s

