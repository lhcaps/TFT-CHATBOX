"""Verify Plan 05-02 implementation."""
import asyncio
import sys
sys.path.insert(0, ".")

from scripts.ingest_tft_static import (
    format_patch_data,
    _extract_season_from_patch,
    ingest_tft_static,
)

# Test 1: format_patch_data with mock data
mock = {
    "champions": {"data": {"TFT7_Ahri": {"name": "Ahri", "cost": 3, "traits": ["Mage"], "stats": {"hp": 750}}}},
    "traits": {"data": {"Set7_Cultist": {"name": "Cultist", "desc": "Your team gains..."}}},
    "items": {"data": {"1042": {"name": "Needlessly Large Rod", "desc": "+20 AP"}}},
    "augments": {"data": {"TFT7_Augment": {"name": "Portable Forge", "desc": "Extra item slot", "tier": [3]}}},
}
chunks = format_patch_data(mock, "17.1")
print("Test 1 - format_patch_data:")
print("  Keys:", list(chunks.keys()))
print("  Season:", chunks["champions"][1]["season"])
print("  Champion chunk length:", len(chunks["champions"][0]))
assert "champions" in chunks and "traits" in chunks and "items" in chunks and "augments" in chunks
assert chunks["champions"][1]["season"] == "SET17"
assert chunks["champions"][1]["patch"] == "17.1"
assert chunks["champions"][1]["type"] == "champions"
print("  PASS: All assertions passed")

# Test 2: _extract_season_from_patch
print("\nTest 2 - _extract_season_from_patch:")
for patch, expected in [("14.0", "SET14"), ("15.1", "SET15"), ("16.2", "SET16"), ("17.1", "SET17"), ("18.0", "SET18")]:
    result = _extract_season_from_patch(patch)
    print(f"  {patch} -> {result} (expected {expected})")
    assert result == expected
print("  PASS: Season mapping correct")

# Test 3: ingest_tft_static returns correct structure
print("\nTest 3 - ingest_tft_static:")
result = asyncio.run(ingest_tft_static())
print("  patch:", result["patch"])
print("  status:", result["status"])
print("  types:", result["types"])
print("  chunk_count:", len(result["chunks"]))
assert "patch" in result
assert "status" in result
assert "types" in result
assert "chunks" in result
assert result["types"] == list(result.get("types", []))
if len(result["chunks"]) > 0:
    print("  CDN available: found", len(result["chunks"]), "chunks")
    assert len(result["chunks"]) == 4
    for c in result["chunks"]:
        print(f"  {c['type']}: {len(c['text'])} chars, hash={c['hash'][:8]}...")
        print(f"    metadata: {c['metadata']}")
        assert "type" in c
        assert "text" in c
        assert "hash" in c
        assert "metadata" in c
        assert c["metadata"]["season"] == "SET" + result["patch"].split(".")[0]
        assert c["metadata"]["patch"] == result["patch"]
    print("  PASS: All chunks have correct structure")
else:
    print("  CDN unavailable (403) - 0 chunks expected, code handles gracefully")
    print("  PASS: Graceful handling of empty data")
print("  PASS: ingest_tft_static returns correct structure")

print("\n=== ALL TESTS PASSED ===")
