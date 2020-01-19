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
