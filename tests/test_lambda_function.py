# pylint: disable=missing-module-docstring, missing-function-docstring

import re

import pytest
import lambda_function as main
from yig.plugins.group import analyze_join_command, analyze_kp_order_command


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
    (1, 1, "クリティカル", main.COLOR_CRITICAL),
    (5, 5, "クリティカル", main.COLOR_CRITICAL),
    (20, 15, "成功", main.COLOR_SUCCESS),
    (100, 100, "成功", main.COLOR_SUCCESS),
    (1, 5, "失敗", main.COLOR_FAILURE),
    (94, 95, "失敗", main.COLOR_FAILURE),
    (95, 96, "ファンブル", main.COLOR_FUMBLE),
    (95, 100, "ファンブル", main.COLOR_FUMBLE),
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
    ("SANC 1/1D3", 100,
     r"成功 【SANチェック】 \d+/100\n【減少値】 \d", main.COLOR_SUCCESS),
    ("SANC 1/1D3", 0,
     r"失敗 【SANチェック】 \d+/0\n【減少値】 \d", main.COLOR_FAILURE),
])
def test_get_sanc_result(cmd, san_val, msg_matcher, color):
    actual_msg, actual_color = main.get_sanc_result(cmd, san_val)
    assert re.match(msg_matcher, actual_msg) is not None
    assert actual_color == color


@pytest.mark.parametrize("text, message, detail, sum_val", [
    ("1D1", "1D1", f"1D1".ljust(80) + "1 [plus] \n", 1),
    ("1D1+1", "1D1+1", f"1D1".ljust(80) +
     "1 [plus] \n" + f"1".ljust(80) + "1 [plus] \n", 2),
])
def test_create_post_message_rolls_result(text, message, detail, sum_val):
    result_message, resule_detail, result_sum = main.create_post_message_rolls_result(
        text)
    assert result_message == message
    assert resule_detail == detail
    assert result_sum == sum_val


@pytest.mark.parametrize("command, exp_status_name, exp_operator, exp_arg", [
    ("u MP+1", "MP", "+", "1"),
    ("u SAN-10", "SAN", "-", "10"),
    ("u HP - 5", "HP", "-", "5"),
])
def test_analyze_update_command(command, exp_status_name, exp_operator, exp_arg):
    result = main.analyze_update_command(command)
    assert result
    status_name, operator, arg = result
    assert status_name == exp_status_name
    assert operator == exp_operator
    assert arg == exp_arg


@pytest.mark.parametrize("command", [
    ("u MP"),
    ("u SAN^10"),
])
def test_analyze_update_command_invalid(command):
    result = main.analyze_update_command(command)
    assert result is None


@pytest.mark.parametrize("command, exp_kp_id", [
    ("join UE63DUJJF", "UE63DUJJF"),
])
def test_analyze_join_command(command, exp_kp_id):
    kp_id = analyze_join_command(command)
    assert kp_id == exp_kp_id


@pytest.mark.parametrize("command, exp_status_name", [
    ("KP ORDER DEX", "DEX"),
    ("KP ORDER 幸運", "幸運"),
])
def test_analyze_kp_order_command(command, exp_status_name):
    status_name = analyze_kp_order_command(command)
    assert status_name == exp_status_name
