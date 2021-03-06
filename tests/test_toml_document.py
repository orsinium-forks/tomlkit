# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import copy
import json
import pickle

from datetime import datetime

import tomlkit
from tomlkit import parse
from tomlkit._utils import _utc


def test_document_is_a_dict(example):
    content = example("example")

    doc = parse(content)

    assert isinstance(doc, dict)
    assert "owner" in doc

    # owner
    owner = doc["owner"]
    assert doc.get("owner") == owner
    assert isinstance(owner, dict)
    assert "name" in owner
    assert owner["name"] == "Tom Preston-Werner"
    assert owner["organization"] == "GitHub"
    assert owner["bio"] == "GitHub Cofounder & CEO\nLikes tater tots and beer."
    assert owner["dob"] == datetime(1979, 5, 27, 7, 32, tzinfo=_utc)

    # database
    database = doc["database"]
    assert isinstance(database, dict)
    assert database["server"] == "192.168.1.1"
    assert database["ports"] == [8001, 8001, 8002]
    assert database["connection_max"] == 5000
    assert database["enabled"] is True

    # servers
    servers = doc["servers"]
    assert isinstance(servers, dict)

    alpha = servers["alpha"]
    assert servers.get("alpha") == alpha
    assert isinstance(alpha, dict)
    assert alpha["ip"] == "10.0.0.1"
    assert alpha["dc"] == "eqdc10"

    beta = servers["beta"]
    assert isinstance(beta, dict)
    assert beta["ip"] == "10.0.0.2"
    assert beta["dc"] == "eqdc10"
    assert beta["country"] == "中国"

    # clients
    clients = doc["clients"]
    assert isinstance(clients, dict)

    data = clients["data"]
    assert isinstance(data, list)
    assert data[0] == ["gamma", "delta"]
    assert data[1] == [1, 2]

    assert clients["hosts"] == ["alpha", "omega"]

    # Products
    products = doc["products"]
    assert isinstance(products, list)

    hammer = products[0]
    assert hammer == {"name": "Hammer", "sku": 738594937}

    nail = products[1]
    assert nail["name"] == "Nail"
    assert nail["sku"] == 284758393
    assert nail["color"] == "gray"

    nail["color"] = "black"
    assert nail["color"] == "black"
    assert doc["products"][1]["color"] == "black"
    assert nail.get("color") == "black"

    content = """foo = "bar"
"""

    doc = parse(content)
    doc.update({"bar": "baz"})

    assert (
        doc.as_string()
        == """foo = "bar"
bar = "baz"
"""
    )

    doc.update({"bar": "boom"})

    assert (
        doc.as_string()
        == """foo = "bar"
bar = "boom"
"""
    )

    assert doc.setdefault("bar", "waldo") == "boom"

    assert (
        doc.as_string()
        == """foo = "bar"
bar = "boom"
"""
    )

    assert doc.setdefault("thud", "waldo") == "waldo"

    assert (
        doc.as_string()
        == """foo = "bar"
bar = "boom"
thud = "waldo"
"""
    )


def test_toml_document_without_super_tables():
    content = """[tool.poetry]
name = "foo"
"""

    doc = parse(content)
    assert "tool" in doc
    assert "poetry" in doc["tool"]

    assert doc["tool"]["poetry"]["name"] == "foo"

    doc["tool"]["poetry"]["name"] = "bar"

    assert (
        doc.as_string()
        == """[tool.poetry]
name = "bar"
"""
    )

    d = {}
    d.update(doc)

    assert "tool" in d


def test_toml_document_with_dotted_keys(example):
    content = example("0.5.0")

    doc = parse(content)

    assert "physical" in doc
    assert "color" in doc["physical"]
    assert "shape" in doc["physical"]
    assert doc["physical"]["color"] == "orange"
    assert doc["physical"]["shape"] == "round"

    assert "site" in doc
    assert "google.com" in doc["site"]
    assert doc["site"]["google.com"]

    assert doc["a"]["b"]["c"] == 1
    assert doc["a"]["b"]["d"] == 2


def test_toml_document_super_table_with_different_sub_sections(example):
    content = example("pyproject")

    doc = parse(content)
    tool = doc["tool"]

    assert "poetry" in tool
    assert "black" in tool


def test_adding_an_element_to_existing_table_with_ws_remove_ws():
    content = """[foo]

[foo.bar]

"""

    doc = parse(content)
    doc["foo"]["int"] = 34

    expected = """[foo]
int = 34

[foo.bar]

"""

    assert expected == doc.as_string()


def test_document_with_aot_after_sub_tables():
    content = """[foo.bar]
name = "Bar"

[foo.bar.baz]
name = "Baz"

[[foo.bar.tests]]
name = "Test 1"
"""

    doc = parse(content)
    assert doc["foo"]["bar"]["tests"][0]["name"] == "Test 1"


def test_document_with_new_sub_table_after_other_table():
    content = """[foo]
name = "Bar"

[bar]
name = "Baz"

[foo.baz]
name = "Test 1"
"""

    doc = parse(content)
    assert doc["foo"]["name"] == "Bar"
    assert doc["bar"]["name"] == "Baz"
    assert doc["foo"]["baz"]["name"] == "Test 1"

    assert doc.as_string() == content


def test_document_with_new_sub_table_after_other_table_delete():
    content = """[foo]
name = "Bar"

[bar]
name = "Baz"

[foo.baz]
name = "Test 1"
"""

    doc = parse(content)

    del doc["foo"]

    assert (
        doc.as_string()
        == """[bar]
name = "Baz"

"""
    )


def test_document_with_new_sub_table_after_other_table_replace():
    content = """[foo]
name = "Bar"

[bar]
name = "Baz"

[foo.baz]
name = "Test 1"
"""

    doc = parse(content)

    doc["foo"] = {"a": "b"}

    assert (
        doc.as_string()
        == """[foo]
a = "b"

[bar]
name = "Baz"

"""
    )


def test_inserting_after_element_with_no_new_line_adds_a_new_line():
    doc = parse("foo = 10")
    doc["bar"] = 11

    expected = """foo = 10
bar = 11
"""

    assert expected == doc.as_string()

    doc = parse("# Comment")
    doc["bar"] = 11

    expected = """# Comment
bar = 11
"""

    assert expected == doc.as_string()


def test_inserting_after_deletion():
    doc = parse("foo = 10\n")
    del doc["foo"]

    doc["bar"] = 11

    expected = """bar = 11
"""

    assert expected == doc.as_string()


def test_toml_document_with_dotted_keys_inside_table(example):
    content = example("0.5.0")

    doc = parse(content)
    t = doc["table"]

    assert "a" in t

    assert t["a"]["b"]["c"] == 1
    assert t["a"]["b"]["d"] == 2
    assert t["a"]["c"] == 3


def test_toml_document_with_super_aot_after_super_table(example):
    content = example("pyproject")

    doc = parse(content)
    aot = doc["tool"]["foo"]

    assert isinstance(aot, list)

    first = aot[0]
    assert first["name"] == "first"

    second = aot[1]
    assert second["name"] == "second"


def test_toml_document_has_always_a_new_line_after_table_header():
    content = """[section.sub]"""

    doc = parse(content)
    assert doc.as_string() == """[section.sub]"""

    doc["section"]["sub"]["foo"] = "bar"
    assert (
        doc.as_string()
        == """[section.sub]
foo = "bar"
"""
    )

    del doc["section"]["sub"]["foo"]

    assert doc.as_string() == """[section.sub]"""


def test_toml_document_is_pickable(example):
    content = example("example")

    doc = parse(content)
    assert pickle.loads(pickle.dumps(doc)).as_string() == content


def test_toml_document_set_super_table_element():
    content = """[site.user]
name = "John"
"""

    doc = parse(content)
    doc["site"]["user"] = "Tom"

    assert (
        doc.as_string()
        == """[site]
user = "Tom"
"""
    )


def test_toml_document_can_be_copied():
    content = "[foo]\nbar=1"

    doc = parse(content)
    doc = copy.copy(doc)

    assert (
        doc.as_string()
        == """[foo]
bar=1"""
    )

    assert doc == {"foo": {"bar": 1}}
    assert doc["foo"]["bar"] == 1
    assert json.loads(json.dumps(doc)) == {"foo": {"bar": 1}}

    doc = parse(content)
    doc = doc.copy()

    assert (
        doc.as_string()
        == """[foo]
bar=1"""
    )

    assert doc == {"foo": {"bar": 1}}
    assert doc["foo"]["bar"] == 1
    assert json.loads(json.dumps(doc)) == {"foo": {"bar": 1}}


def test_getting_inline_table_is_still_an_inline_table():
    content = """\
[tool.poetry]
name = "foo"

[tool.poetry.dependencies]
"""

    doc = parse(content)
    poetry_section = doc["tool"]["poetry"]
    dependencies = poetry_section["dependencies"]
    dependencies["foo"] = tomlkit.inline_table()
    dependencies["foo"]["version"] = "^2.0"
    dependencies["foo"]["source"] = "local"
    doc["tool"]["poetry"] = poetry_section

    assert (
        """\
[tool.poetry]
name = "foo"

[tool.poetry.dependencies]
foo = {version = "^2.0", source = "local"}
"""
        == doc.as_string()
    )


def test_declare_sub_table_with_intermediate_table():
    content = """
[students]
tommy = 87
mary = 66

[subjects]
maths = "maths"
english = "english"

[students.bob]
score = 91
"""

    doc = parse(content)
    assert {"tommy": 87, "mary": 66, "bob": {"score": 91}} == doc["students"]
    assert {"tommy": 87, "mary": 66, "bob": {"score": 91}} == doc.get("students")
