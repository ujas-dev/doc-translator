import os
import tempfile
import pytest
from unittest.mock import MagicMock, patch

from apps.documents.pdf_layout import _is_formula


class TestIsFormula:
    def test_detects_latex_formula(self):
        assert _is_formula(r"E = mc^2") is True

    def test_detects_inline_latex(self):
        assert _is_formula(r"\frac{a}{b}") is True

    def test_detects_summation(self):
        assert _is_formula(r"\sum_{i=1}^{n}") is True

    def test_detects_integral(self):
        assert _is_formula(r"\int_0^1 f(x) dx") is True

    def test_detects_square_root(self):
        assert _is_formula(r"\sqrt{x}") is True

    def test_detects_subscript_superscript(self):
        assert _is_formula(r"x_1 + y^2") is True

    def test_plain_text_not_formula(self):
        assert _is_formula("") is False
        assert _is_formula("x") is False

    def test_empty_string_not_formula(self):
        assert _is_formula("") is False

    def test_single_variable_not_formula(self):
        assert _is_formula("x") is False

    def test_detects_greek_letters(self):
        assert _is_formula(r"\alpha + \beta") is True

    def test_detects_matrix(self):
        assert _is_formula(r"\begin{matrix}") is True
