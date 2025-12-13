import hashlib
import time
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Block:
    index: int
    previous_hash: str
    timestamp: float
    data: str
    nonce: int = 0
    hash: Optional[str] = None

    def header(self) -> str:
        """Return the string that will be hashed for PoW."""
        return f"{self.index}|{self.previous_hash}|{self.timestamp:.6f}|{self.data}|{self.nonce}"

def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode('utf-8')).hexdigest()

def valid_proof(hash_hex: str, difficulty: int) -> bool:
    """
    Simple PoW rule: hash must start with `difficulty` leading hex zeros.
    Example: difficulty=4 => hash starts with "0000".
    """
    return hash_hex.startswith('0' * difficulty)

def mine_block(block: Block, difficulty: int, max_nonce: int = 10_000_000) -> Block:
    """
    Brute-force search for a nonce that satisfies the proof-of-work.

    Parameters
    - block: Block object (nonce and hash will be updated)
    - difficulty: number of leading hex zeros required in hash
    - max_nonce: safety cap to avoid infinite loops (increase as needed)

    Returns the mined Block (with nonce and hash set). Raises RuntimeError if not found.
    """
    start = time.time()
    for nonce in range(max_nonce):
        block.nonce = nonce
        h = sha256_hex(block.header())
        if valid_proof(h, difficulty):
            block.hash = h
            elapsed = time.time() - start
            print(f"✅ Mined block #{block.index} in {nonce+1} attempts, time: {elapsed:.3f}s, nonce: {nonce}")
            print(f"   hash: {h}")
            return block
        # optional: occasionally print progress (uncomment if desired)
        # if nonce % 1000000 == 0 and nonce > 0:
        #     print(f"tried {nonce} nonces...")
    raise RuntimeError(f"Failed to mine block within {max_nonce} nonces")

def validate_block(block: Block, difficulty: int) -> bool:
    """
    Validates that:
      1) hash matches header (index, prev_hash, timestamp, data, nonce)
      2) hash satisfies difficulty (PoW)
    """
    if block.hash is None:
        return False
    calc_hash = sha256_hex(block.header())
    if calc_hash != block.hash:
        print("Invalid: stored hash does not match calculated hash.")
        return False
    if not valid_proof(block.hash, difficulty):
        print("Invalid: proof-of-work requirement not satisfied.")
        return False
    return True

# --- Demo / usage ---
if __name__ == "__main__":
    # Example genesis block
    genesis = Block(index=0, previous_hash="0"*64, timestamp=time.time(), data="Genesis Block")
    difficulty = 4  # adjust difficulty: 1..6 is fast for demo; bigger => slower

    # Mine genesis
    mined_genesis = mine_block(genesis, difficulty)

    # Validate
    print("Validating genesis:", validate_block(mined_genesis, difficulty))

    # Create & mine another block
    block1 = Block(index=1, previous_hash=mined_genesis.hash, timestamp=time.time(), data="Alice -> Bob: 5 BTC")
    mined_block1 = mine_block(block1, difficulty)
    print("Validating block 1:", validate_block(mined_block1, difficulty))

    # Tamper and show validation fails
    mined_block1.data = "Alice -> Bob: 50 BTC"  # attacker modifies data but doesn't re-mine
    print("After tampering, validation:", validate_block(mined_block1, difficulty))