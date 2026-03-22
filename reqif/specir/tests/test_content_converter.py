"""Tests for the content_converter module (AST/HTML → Markdown/HTML).

Self-contained — only requires pandoc. Each test builds Pandoc AST JSON inline.
"""
from __future__ import annotations

import json
import os
import sqlite3
import tempfile
import unittest

from reqif.specir.content_converter import (
    ast_to_html,
    ast_to_markdown,
    attr_xhtml_to_markdown,
    body_to_html,
    body_to_markdown,
    get_pandoc,
    html_to_markdown,
)


def _skip_no_pandoc(test):
    if not get_pandoc():
        test.skipTest("pandoc not found")


# ── AST → Markdown ──────────────────────────────────────────────────────

class TestAstToMarkdown(unittest.TestCase):

    def test_simple_para(self):
        _skip_no_pandoc(self)
        blocks = [{"t": "Para", "c": [
            {"t": "Str", "c": "Hello"},
            {"t": "Space"},
            {"t": "Str", "c": "world."},
        ]}]
        md = ast_to_markdown(json.dumps(blocks), strip_headers=False)
        self.assertIsNotNone(md)
        self.assertIn("Hello world.", md)

    def test_strips_headers(self):
        _skip_no_pandoc(self)
        blocks = [
            {"t": "Header", "c": [2, ["hid", [], []], [{"t": "Str", "c": "Title"}]]},
            {"t": "Para", "c": [{"t": "Str", "c": "Body"}]},
        ]
        md = ast_to_markdown(json.dumps(blocks), strip_headers=True)
        self.assertIsNotNone(md)
        self.assertNotIn("Title", md)
        self.assertIn("Body", md)

    def test_strips_data_pos(self):
        _skip_no_pandoc(self)
        blocks = [{"t": "Para", "c": [
            {"t": "Link", "c": [
                ["", [], [["data-pos", "1:1-2:1"]]],
                [{"t": "Str", "c": "ref"}],
                ["#target", ""],
            ]},
        ]}]
        md = ast_to_markdown(json.dumps(blocks), strip_headers=False)
        self.assertIsNotNone(md)
        self.assertNotIn("data-pos", md)
        self.assertIn("ref", md)

    def test_strips_definition_list(self):
        _skip_no_pandoc(self)
        blocks = [
            {"t": "Para", "c": [{"t": "Str", "c": "Body"}]},
            {"t": "DefinitionList", "c": [
                [[{"t": "Str", "c": "status"}],
                 [[{"t": "Para", "c": [{"t": "Str", "c": "Approved"}]}]]]
            ]},
        ]
        md = ast_to_markdown(json.dumps(blocks), strip_headers=True)
        self.assertIsNotNone(md)
        self.assertIn("Body", md)
        self.assertNotIn("status", md)

    def test_strips_blockquote(self):
        _skip_no_pandoc(self)
        blocks = [
            {"t": "Para", "c": [{"t": "Str", "c": "Content"}]},
            {"t": "BlockQuote", "c": [
                {"t": "Para", "c": [{"t": "Str", "c": "description:"}]}
            ]},
        ]
        md = ast_to_markdown(json.dumps(blocks), strip_headers=True)
        self.assertIsNotNone(md)
        self.assertIn("Content", md)
        self.assertNotIn("description", md)

    def test_strips_relation_para(self):
        _skip_no_pandoc(self)
        blocks = [
            {"t": "Para", "c": [{"t": "Str", "c": "Body"}]},
            {"t": "Para", "c": [
                {"t": "Link", "c": [
                    ["", [], []], [{"t": "Str", "c": "REQ-001"}], ["@", ""],
                ]},
            ]},
        ]
        md = ast_to_markdown(json.dumps(blocks), strip_headers=True)
        self.assertIsNotNone(md)
        self.assertIn("Body", md)
        self.assertNotIn("REQ-001", md)

    def test_unwraps_trivial_divs(self):
        _skip_no_pandoc(self)
        blocks = [{"t": "Div", "c": [
            ["", [], []],
            [{"t": "Para", "c": [{"t": "Str", "c": "Inside"}]}],
        ]}]
        md = ast_to_markdown(json.dumps(blocks), strip_headers=False)
        self.assertIsNotNone(md)
        self.assertIn("Inside", md)
        self.assertNotIn("<div>", md)

    def test_unwraps_structural_divs(self):
        _skip_no_pandoc(self)
        blocks = [{"t": "Div", "c": [
            ["", ["spec-object"], [["custom-style", "SpecObject"]]],
            [
                {"t": "Div", "c": [
                    ["", ["spec-object-body"], []],
                    [{"t": "Para", "c": [{"t": "Str", "c": "Body"}]}],
                ]},
                {"t": "Div", "c": [
                    ["", ["spec-object-attributes"], []],
                    [{"t": "DefinitionList", "c": []}],
                ]},
            ],
        ]}]
        md = ast_to_markdown(json.dumps(blocks), strip_headers=True)
        self.assertIsNotNone(md)
        self.assertIn("Body", md)

    def test_merges_plain_blocks(self):
        _skip_no_pandoc(self)
        blocks = [
            {"t": "Plain", "c": [{"t": "Str", "c": "Hello"}]},
            {"t": "Plain", "c": [{"t": "Space"}]},
            {"t": "Plain", "c": [{"t": "Str", "c": "world"}]},
        ]
        md = ast_to_markdown(json.dumps(blocks), strip_headers=False)
        self.assertIsNotNone(md)
        self.assertIn("Hello world", md)
        self.assertNotIn("Hello\n", md)

    def test_none_returns_none(self):
        self.assertIsNone(ast_to_markdown(None))
        self.assertIsNone(ast_to_markdown(""))
        self.assertIsNone(ast_to_markdown("not json"))

    def test_empty_blocks_returns_none(self):
        self.assertIsNone(ast_to_markdown("[]"))


# ── HTML → Markdown ─────────────────────────────────────────────────────

class TestHtmlToMarkdown(unittest.TestCase):

    def test_simple(self):
        _skip_no_pandoc(self)
        md = html_to_markdown("<p>Hello <strong>world</strong></p>")
        self.assertIsNotNone(md)
        self.assertIn("Hello", md)
        self.assertIn("**world**", md)

    def test_none_returns_none(self):
        self.assertIsNone(html_to_markdown(None))
        self.assertIsNone(html_to_markdown(""))


# ── Fallback chains (Markdown) ──────────────────────────────────────────

class TestMarkdownFallbacks(unittest.TestCase):

    def test_body_prefers_ast(self):
        _skip_no_pandoc(self)
        ast = json.dumps([{"t": "Para", "c": [{"t": "Str", "c": "FromAST"}]}])
        md = body_to_markdown(ast_json=ast, content_xhtml="<p>FromHTML</p>")
        self.assertIn("FromAST", md)
        self.assertNotIn("FromHTML", md)

    def test_body_falls_back_to_html(self):
        _skip_no_pandoc(self)
        md = body_to_markdown(ast_json=None, content_xhtml="<p>FromHTML</p>")
        self.assertIn("FromHTML", md)

    def test_body_returns_none_when_empty(self):
        self.assertIsNone(body_to_markdown())

    def test_attr_prefers_ast(self):
        _skip_no_pandoc(self)
        ast = json.dumps([{"t": "Plain", "c": [{"t": "Str", "c": "AST"}]}])
        md = attr_xhtml_to_markdown(ast_json=ast, xhtml_value="<p>HTML</p>", string_value="plain")
        self.assertIn("AST", md)

    def test_attr_falls_back_to_html(self):
        _skip_no_pandoc(self)
        md = attr_xhtml_to_markdown(xhtml_value="<p>HTML</p>", string_value="plain")
        self.assertIn("HTML", md)

    def test_attr_falls_back_to_string(self):
        md = attr_xhtml_to_markdown(string_value="plain text")
        self.assertEqual(md, "plain text")

    def test_attr_none_when_empty(self):
        self.assertIsNone(attr_xhtml_to_markdown())


# ── AST → HTML ──────────────────────────────────────────────────────────

class TestAstToHtml(unittest.TestCase):

    def test_simple_para(self):
        _skip_no_pandoc(self)
        blocks = [{"t": "Para", "c": [
            {"t": "Str", "c": "Hello"},
            {"t": "Space"},
            {"t": "Strong", "c": [{"t": "Str", "c": "world"}]},
        ]}]
        html = ast_to_html(json.dumps(blocks), strip_headers=False)
        self.assertIsNotNone(html)
        self.assertIn("Hello", html)
        self.assertIn("<strong>world</strong>", html)

    def test_strips_headers(self):
        _skip_no_pandoc(self)
        blocks = [
            {"t": "Header", "c": [2, ["h", [], []], [{"t": "Str", "c": "Title"}]]},
            {"t": "Para", "c": [{"t": "Str", "c": "Body"}]},
        ]
        html = ast_to_html(json.dumps(blocks), strip_headers=True)
        self.assertIsNotNone(html)
        self.assertNotIn("Title", html)
        self.assertIn("Body", html)

    def test_body_to_html_prefers_content_xhtml(self):
        html = body_to_html(
            ast_json=json.dumps([{"t": "Para", "c": [{"t": "Str", "c": "AST"}]}]),
            content_xhtml="<p>Existing HTML</p>",
        )
        self.assertEqual(html, "<p>Existing HTML</p>")

    def test_body_to_html_falls_back_to_ast(self):
        _skip_no_pandoc(self)
        html = body_to_html(
            ast_json=json.dumps([{"t": "Para", "c": [{"t": "Str", "c": "FromAST"}]}]),
            content_xhtml=None,
        )
        self.assertIsNotNone(html)
        self.assertIn("FromAST", html)

    def test_body_to_html_empty(self):
        self.assertIsNone(body_to_html())

    def test_none_input(self):
        self.assertIsNone(ast_to_html(None))
        self.assertIsNone(ast_to_html(""))
        self.assertIsNone(ast_to_html("[]"))


if __name__ == "__main__":
    unittest.main()
