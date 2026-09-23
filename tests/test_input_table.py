"""Reading lists in whatever shape they arrive, and turning each row into one
address the geocoder understands."""

import pytest

from input_table import build_address, build_label, read_people


def write(tmp_path, name, text, bom=False):
    path = tmp_path / name
    path.write_text(("﻿" if bom else "") + text, encoding="utf-8")
    return path


def test_contact_export_is_stitched_into_one_address(tmp_path):
    path = write(tmp_path, "contacts.csv",
                 "First Name,Last Name,Street Address,Street Address 2,City,State,Zip,Email\n"
                 "Maria,Gonzalez,1660 Tully Rd,Apt 12,San Jose,CA,95122,maria@example.org\n")
    rows, columns, roles = read_people(path)
    assert columns == ["First Name", "Last Name", "Street Address", "Street Address 2",
                       "City", "State", "Zip", "Email"]
    assert build_address(rows[0], roles) == "1660 Tully Rd, San Jose, CA 95122"
    assert build_label(rows[0], roles) == "Maria Gonzalez"


def test_unit_line_is_kept_but_never_searched(tmp_path):
    path = write(tmp_path, "contacts.csv",
                 "Street Address,Street Address 2,City,State,Zip\n"
                 "1660 Tully Rd,Apt 12,San Jose,CA,95122\n")
    rows, _, roles = read_people(path)
    assert roles["unit"] == "Street Address 2"
    assert "Apt" not in build_address(rows[0], roles)
    assert rows[0]["Street Address 2"] == "Apt 12"


@pytest.mark.parametrize("headers", [
    "street_address,city,state,zip_code",
    "ADDRESS LINE 1,City,State,Postal Code",
    "Mailing Address,Town,State,ZIP",
])
def test_header_spellings_are_recognized(tmp_path, headers):
    path = write(tmp_path, "list.csv", f"{headers}\n1660 Tully Rd,San Jose,CA,95122\n")
    rows, _, roles = read_people(path)
    assert build_address(rows[0], roles) == "1660 Tully Rd, San Jose, CA 95122"


def test_excel_byte_order_mark_does_not_hide_the_first_column(tmp_path):
    path = write(tmp_path, "excel.csv", "name,address\nJo,\"1660 Tully Rd, San Jose, CA 95122\"\n",
                 bom=True)
    rows, columns, roles = read_people(path)
    assert columns[0] == "name"
    assert build_label(rows[0], roles) == "Jo"


def test_semicolon_separated_file(tmp_path):
    path = write(tmp_path, "euro.csv", "Name;Address;City;State;Zip\nJo;70 N First St;Campbell;CA;95008\n")
    rows, _, roles = read_people(path)
    assert build_address(rows[0], roles) == "70 N First St, Campbell, CA 95008"


def test_plain_text_list_one_address_per_line(tmp_path):
    # The commas in each address must not be mistaken for a header row.
    path = write(tmp_path, "list.txt",
                 "1660 Tully Rd, San Jose, CA 95122\n"
                 "Alex Lee | 70 N First St, Campbell, CA 95008\n\n")
    rows, columns, roles = read_people(path)
    assert columns == ["name", "address"]
    assert [build_address(r, roles) for r in rows] == [
        "1660 Tully Rd, San Jose, CA 95122", "70 N First St, Campbell, CA 95008"]
    assert [r["name"] for r in rows] == ["", "Alex Lee"]


def test_text_pasted_from_a_spreadsheet_keeps_its_columns(tmp_path):
    path = write(tmp_path, "pasted.txt",
                 "First Name\tStreet Address\tCity\tState\tZip\nDana\t456 W Olive Ave\tSunnyvale\tCA\t94086\n")
    rows, columns, roles = read_people(path)
    assert "First Name" in columns
    assert build_address(rows[0], roles) == "456 W Olive Ave, Sunnyvale, CA 94086"


def test_missing_street_still_produces_a_searchable_remainder(tmp_path):
    path = write(tmp_path, "list.csv", "Name,Address,City,State,Zip\nNo Street,,San Jose,CA,95122\n")
    rows, _, roles = read_people(path)
    assert build_address(rows[0], roles) == "San Jose, CA 95122"


def test_blank_rows_are_skipped(tmp_path):
    path = write(tmp_path, "list.csv", "name,address\nA,\"1 Main St, X, CA\"\n,\n\n")
    rows, _, _ = read_people(path)
    assert len(rows) == 1


def test_list_without_an_address_column_is_refused_clearly(tmp_path):
    path = write(tmp_path, "list.csv", "Nickname,Phone\nJo,555-1234\n")
    with pytest.raises(ValueError, match="couldn't find an address column.*Nickname"):
        read_people(path)
