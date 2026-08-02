import argparse
import json
import os
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_DIR = ROOT / "astron" / "databases"
ASTRONDB_DIR = DB_DIR / "astrondb"
INFO_YAML = ASTRONDB_DIR / "info.yaml"
ACCOUNTS_JSON = DB_DIR / "accounts.json"


def _read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _write_text(p: Path, s: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    # Python 3.9 Path.write_text doesn't accept newline=
    p.write_text(s, encoding="utf-8")


def _alloc_ids(count: int) -> list[int]:
    m = re.search(r"^\s*next:\s*(\d+)\s*$", _read_text(INFO_YAML), flags=re.M)
    if not m:
        raise RuntimeError(f"Could not find next id in {INFO_YAML}")
    next_id = int(m.group(1))
    ids = list(range(next_id, next_id + count))
    _write_text(INFO_YAML, f"next: {next_id + count}\n")
    return ids


def _load_accounts_map() -> dict[str, int]:
    if not ACCOUNTS_JSON.exists():
        return {}
    return {k: int(v) for k, v in json.loads(_read_text(ACCOUNTS_JSON)).items()}


def _save_accounts_map(m: dict[str, int]) -> None:
    _write_text(ACCOUNTS_JSON, json.dumps(m, indent=2, sort_keys=True) + "\n")


def _render_account_yaml(account_id: int, username: str, toon_ids: list[int]) -> str:
    # Mirrors existing AstronAccount yaml shape in this repo.
    av_set = toon_ids[:6] + [0] * max(0, 6 - len(toon_ids))
    av_set_str = "[" + ", ".join(str(x) for x in av_set) + "]"
    return (
        f"id: {account_id}\n"
        f"class: AstronAccount\n"
        f"fields:\n"
        f"  ACCOUNT_AV_SET: \"{av_set_str}\"\n"
        f"  ESTATE_ID: 0\n"
        f"  ACCOUNT_AV_SET_DEL: \"[]\"\n"
        f"  CREATED: \"\\\"{_now_string()}\\\"\"\n"
        f"  LAST_LOGIN: \"\\\"{_now_string()}\\\"\"\n"
        f"  ACCOUNT_ID: \"\\\"{username}\\\"\"\n"
        f"  ACCESS_LEVEL: \"\\\"SYSTEM_ADMIN\\\"\"\n"
    )


def _now_string() -> str:
    # Keep format similar to existing DB. Exact value isn't important.
    import datetime

    return datetime.datetime.now().strftime("%a %b %d %H:%M:%S %Y")


def _render_toon_yaml(toon_id: int, toon_name: str, default_shard: int, default_zone: int) -> str:
    # Use an existing toon as template if available, for maximum compatibility.
    template_path = ASTRONDB_DIR / "100000001.yaml"
    if template_path.exists():
        s = _read_text(template_path)
        s = re.sub(r"^id:\s*\d+\s*$", f"id: {toon_id}", s, flags=re.M)
        s = re.sub(r"^\s*setName:\s*\(.+\)\s*$", f"  setName: (\"{toon_name}\")", s, flags=re.M)
        s = re.sub(r"^\s*setDefaultShard:\s*\(\d+\)\s*$", f"  setDefaultShard: ({default_shard})", s, flags=re.M)
        s = re.sub(r"^\s*setDefaultZone:\s*\(\d+\)\s*$", f"  setDefaultZone: ({default_zone})", s, flags=re.M)
        return s

    # Fallback: minimal toon fields (may be insufficient for gameplay depending on server/client).
    return (
        f"id: {toon_id}\n"
        f"class: DistributedToon\n"
        f"fields:\n"
        f"  setName: (\"{toon_name}\")\n"
        f"  setAccountName: (\"\")\n"
        f"  setDefaultShard: ({default_shard})\n"
        f"  setDefaultZone: ({default_zone})\n"
        f"  setMaxHp: (15)\n"
        f"  setHp: (15)\n"
        f"  setMoney: (0)\n"
        f"  setMaxMoney: (40)\n"
        f"  setTutorialAck: (1)\n"
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="Create a local Astron test account + toon in YAML DB.")
    ap.add_argument("--username", required=True)
    ap.add_argument("--toon-name", default="Test Toon")
    ap.add_argument("--default-shard", type=int, default=401000001)
    ap.add_argument("--default-zone", type=int, default=22000)
    args = ap.parse_args()

    if not INFO_YAML.exists():
        raise SystemExit(f"Missing {INFO_YAML} (is astron yaml db set up?)")

    accounts = _load_accounts_map()
    if args.username in accounts:
        raise SystemExit(f"Username already exists in accounts.json: {args.username}")

    account_id, toon_id = _alloc_ids(2)

    accounts[args.username] = account_id
    _save_accounts_map(accounts)

    account_yaml = _render_account_yaml(account_id, args.username, [toon_id])
    toon_yaml = _render_toon_yaml(toon_id, args.toon_name, args.default_shard, args.default_zone)

    _write_text(ASTRONDB_DIR / f"{account_id}.yaml", account_yaml)
    _write_text(ASTRONDB_DIR / f"{toon_id}.yaml", toon_yaml)

    print(f"Created account '{args.username}' -> {account_id}")
    print(f"Created toon '{args.toon_name}' -> {toon_id} (shard={args.default_shard}, zone={args.default_zone})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

