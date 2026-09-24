"""Reads the input list in whatever shape it arrives — a contact export with
separate street/city/state/zip columns, a simple name+address sheet, or a
plain .txt list of addresses — and works out how to build one address string
per person for the geocoder.

Every original column is kept as-is and written back out, so names, emails and
phone numbers stay in their own fields.
"""

import csv
from pathlib import Path

# Header names recognized for each part of an address, in priority order.
# Compared after stripping everything but letters and digits, so "Street
# Address 2", "street_address_2" and "ADDRESS LINE 2" all look the same.
ROLE_HEADERS = {
    "street": ["streetaddress", "streetaddress1", "addressline1", "address1", "address",
               "street", "mailingaddress", "homeaddress", "residenceaddress", "addr", "addr1"],
    "unit": ["streetaddress2", "addressline2", "address2", "unit", "apt", "apartment",
             "suite", "ste", "unitnumber", "addr2"],
    "city": ["city", "town", "mailingcity", "citytown"],
    "state": ["state", "mailingstate", "stateprovince", "province"],
    "zip": ["zip", "zipcode", "postalcode", "postcode", "mailingzip"],
}


def normalize(header: str) -> str:
    return "".join(ch for ch in header.lower() if ch.isalnum())


def detect_roles(fieldnames: list[str]) -> dict[str, str]:
    """Maps each role to the actual header that fills it, where one exists."""
    by_normalized = {}
    for header in fieldnames:
        by_normalized.setdefault(normalize(header), header)
    roles = {}
    for role, candidates in ROLE_HEADERS.items():
        for candidate in candidates:
            if candidate in by_normalized and by_normalized[candidate] not in roles.values():
                roles[role] = by_normalized[candidate]
                break
    return roles


def build_address(row: dict, roles: dict) -> str:
    """Joins the address columns into one line the geocoder understands, e.g.
    "1660 Tully Rd, San Jose, CA 95122". The unit/apartment column is left out
    on purpose — the Census geocoder often fails to match an address that
    carries one, and it isn't needed to place a point on a map."""
    def part(role):
        return (row.get(roles[role]) or "").strip() if role in roles else ""

    state_zip = " ".join(p for p in [part("state"), part("zip")] if p)
    pieces = [part("street"), part("city"), state_zip]
    return ", ".join(p for p in pieces if p)


def describe_roles(roles: dict) -> str:
    used = [roles[r] for r in ("street", "city", "state", "zip") if r in roles]
    description = f"address from {' + '.join(used)}" if used else "no address columns found"
    if "unit" in roles:
        description += f"; {roles['unit']} kept in the output but not searched"
    return description


def _read_delimited(path: Path) -> tuple[list[dict], list[str]]:
    with open(path, newline="", encoding="utf-8-sig") as f:
        sample = f.read(8192)
        f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",\t;|")
        except csv.Error:
            dialect = csv.excel
        reader = csv.DictReader(f, dialect=dialect)
        rows = [row for row in reader if any((v or "").strip() for v in row.values())]
        return rows, list(reader.fieldnames or [])


def _read_lines(path: Path) -> tuple[list[dict], list[str]]:
    """A .txt with no header row: one address per line, optionally "Name | address"."""
    rows = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line:
            continue
        name, _, address = line.partition("|")
        rows.append({"name": name.strip(), "address": address.strip()} if address
                    else {"name": "", "address": name.strip()})
    return rows, ["name", "address"]


def has_header_row(path: Path) -> bool:
    """True if the first line names columns rather than holding an address.
    Checked by looking for a recognized column name, since an address line is
    full of commas too ("1660 Tully Rd, San Jose, CA 95122")."""
    first_line = next(iter(path.read_text(encoding="utf-8-sig").splitlines()), "")
    known = {name for names in ROLE_HEADERS.values() for name in names}
    for delimiter in ["\t", ",", ";", "|"]:
        if any(normalize(field) in known for field in first_line.split(delimiter)):
            return True
    return False


def read_people(path: Path) -> tuple[list[dict], list[str], dict]:
    """Returns (rows, fieldnames, roles). A .txt file is treated as one address
    per line unless its first line looks like a header row of columns."""
    if path.suffix.lower() == ".txt" and not has_header_row(path):
        rows, fieldnames = _read_lines(path)
    else:
        rows, fieldnames = _read_delimited(path)

    if not rows:
        raise ValueError(f"{path} has no rows.")

    roles = detect_roles(fieldnames)
    if "street" not in roles:
        raise ValueError(
            f"{path}: couldn't find an address column. Columns found: {fieldnames}. "
            f"Expected one named something like: {', '.join(ROLE_HEADERS['street'][:5])}."
        )
    return rows, fieldnames, roles
