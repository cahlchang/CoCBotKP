# pylint: disable=missing-module-docstring, missing-function-docstring

import re

import pytest
import lambda_function as main


def test_2():
    msg = "【test_user】TEST\nHP 4/5\u3000\u3000MP 4/5\u3000\u3000DEX 8\u3000\u3000SAN 10/10"
    assert main.get_status_message("TEST",
                                   {"name": "test_user",
                                    "HP": 5,
                                    "MP": 5,
                                    "DEX": 8,
                                    "現在SAN": 10,
                                    "SAN": 15},
                                   {"HP": -1,
                                    "MP": -1}) == msg


@pytest.mark.parametrize("target, actual, exp_msg, exp_color", [
    (100, 1, "成功", main.COLOR_CRITICAL),
    (100, 5, "成功", main.COLOR_CRITICAL),
    (20, 15, "成功", main.COLOR_SUCCESS),
    (100, 100, "成功", main.COLOR_SUCCESS),
    (94, 95, "失敗", main.COLOR_FAILURE),
    (95, 96, "失敗", main.COLOR_FUMBLE),
    (95, 100, "失敗", main.COLOR_FUMBLE),
])
def test_judge_1d100(target, actual, exp_msg, exp_color):
    msg, color = main.judge_1d100(target, actual)
    assert msg == exp_msg
    assert color == exp_color


@pytest.mark.parametrize("cmd, result", [
    ("0/1", ("0", "1")),
    ("1/1D3", ("1", "1D3")),
    ("1D3/1D8", ("1D3", "1D8")),
    ("1", None),
    ("1DD3/1D8", None),
    ("1D3/1DD8", None),
    ("hoge/1D3", None),
    ("1/hoge", None),
])
def test_split_alternative_roll_or_value(cmd, result):
    assert main.split_alternative_roll_or_value(cmd) == result


@pytest.mark.parametrize("text, count, min_val, max_val", [
    ("1D6", 1, 1, 6),
    ("3D6", 3, 1, 6),
    ("1d6", 1, 0, 0),
])
def test_eval_roll_or_value_for_roll(text, count, min_val, max_val):
    results = main.eval_roll_or_value(text)
    assert len(results) == count
    for val in results:
        assert min_val <= val
        assert val <= max_val


@pytest.mark.parametrize("text, val", [
    ("0", 0),
    ("1", 1),
    ("hoge", 0),
    ("100a", 0),
])
def test_eval_roll_or_value_for_value(text, val):
    results = main.eval_roll_or_value(text)
    assert len(results) == 1
    assert results[0] == val


@pytest.mark.parametrize("text, expected", [
    ("sanc", "SANC"),
    ("  sanc 1d100    ", "SANC 1D100"),
    ("  1d100 ", "1D100"),
])
def test_format_as_command(text, expected):
    assert main.format_as_command(text) == expected


@pytest.mark.parametrize("cmd, san_val, msg_matcher, color", [
    ("SANC", 100, r"成功 【SANチェック】 \d+/100", main.COLOR_SUCCESS),
    ("SANC", 0, r"失敗 【SANチェック】 \d+/0", main.COLOR_FAILURE),
])
def test_get_sanc_result(cmd, san_val, msg_matcher, color):
    actual_msg, actual_color = main.get_sanc_result(cmd, san_val)
    assert re.match(msg_matcher, actual_msg) is not None
    assert actual_color == color
