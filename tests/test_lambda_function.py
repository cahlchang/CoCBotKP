from lambda_function import get_status_message


def test_2():
    msg = "【test_user】TEST\nHP 4/5\u3000\u3000MP 4/5\u3000\u3000DEX 8\u3000\u3000SAN 10/10"
    assert get_status_message("TEST",
                              {"name": "test_user",
                               "HP": 5,
                               "MP": 5,
                               "DEX": 8,
                               "現在SAN": 10,
                               "SAN": 15},
                              {"HP": -1,
                               "MP": -1}) == msg
