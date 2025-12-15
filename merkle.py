import hashlib
from typing import List, Tuple

def verify_merkle_proof(
    leaf_value: str,
    proof: List[Tuple[bytes, str]],
    root: bytes
) -> bool:
    current_hash = hash_leaf(leaf_value)

    for sibling_hash, direction in proof:
        if direction == "right":
            current_hash = hash_pair(current_hash, sibling_hash)
        else:
            current_hash = hash_pair(sibling_hash, current_hash)

    return current_hash == root

def sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def hash_leaf(value: str) -> bytes:
    return sha256(value.encode())


def hash_pair(left: bytes, right: bytes) -> bytes:
    return sha256(left + right)


class MerkleTree:
    def __init__(self, values: List[str]):
        if not values:
            raise ValueError("Cannot build Merkle Tree with no values")

        self.values = values
        self.leaves = [hash_leaf(v) for v in values]
        self.levels = [self.leaves]
        self._build_tree()

    def _build_tree(self):
        current_level = self.leaves

        while len(current_level) > 1:
            next_level = []

            # If odd number of nodes, duplicate last
            if len(current_level) % 2 == 1:
                current_level.append(current_level[-1])

            for i in range(0, len(current_level), 2):
                parent = hash_pair(current_level[i], current_level[i + 1])
                next_level.append(parent)

            self.levels.append(next_level)
            current_level = next_level

    @property
    def root(self) -> bytes:
        return self.levels[-1][0]

    def get_proof(self, index: int) -> List[Tuple[bytes, str]]:
        """
        Returns a Merkle proof for the leaf at `index`.
        Each proof item is (sibling_hash, direction)
        direction is either 'left' or 'right'
        """
        if index < 0 or index >= len(self.leaves):
            raise IndexError("Leaf index out of range")

        proof = []
        current_index = index

        for level in self.levels[:-1]:
            if current_index % 2 == 0:
                sibling_index = current_index + 1
                direction = "right"
            else:
                sibling_index = current_index - 1
                direction = "left"

            if sibling_index >= len(level):
                sibling_index = current_index

            proof.append((level[sibling_index], direction))
            current_index //= 2

        return proof


data = ["tx1", "tx2", "tx3", "tx4", "tx5"]

tree = MerkleTree(data)

print("Merkle Root:", tree.root.hex())

# Generate proof for "tx3"
index = data.index("tx3")
proof = tree.get_proof(index)

print("\nMerkle Proof:")
for h, d in proof:
    print(d, h.hex())

# Verify proof
is_valid = verify_merkle_proof("tx3", proof, tree.root)
print("\nProof valid?", is_valid)