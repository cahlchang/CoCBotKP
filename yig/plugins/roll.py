import re
import random
import math
import json
from typing import List, Tuple
from concurrent import futures

from yig.bot import listener, RE_MATCH_FLAG, RE_NOPOST_COMMANG_FLAG, LAST_EVALUATION_FLAG
from yig.util.data import get_user_param, get_state_data ,set_state_data, get_status_message, post_command, post_result, get_basic_status, write_session_data, read_session_data
from yig.util.view import get_pc_image_url
import yig.config


@listener(r"sanc.*", RE_MATCH_FLAG)
def sanity_check(bot):
    """:ghost: *san check*\n`/cc sanc`\n`/cc sanc [safe_point]/[fail_point]`"""
    state_data = get_state_data(bot.team_id, bot.user_id)
    param = get_user_param(bot.team_id, bot.user_id, state_data["pc_id"])
    c_san = int(param["現在SAN"])
    if "SAN" in state_data:
        d_san = int(state_data["SAN"])
    else:
        d_san = 0
    sum_san = c_san + d_san
    message, color = get_sanc_result(bot.key, sum_san)
    return message, color


@listener(r"^\d+[dD]\d*.*", RE_MATCH_FLAG)
def dice_roll(bot):
    """:game_die: *dice roll*\n`/cc [X]D[Y]`\n`/cc [X]d[Y][+|-][X]d[Y][+|-][N]`"""
    str_message, str_detail, sum_result = create_post_message_rolls_result(bot.key)
    return f"*{sum_result}* 【ROLLED】\n {str_detail}", "#4169e1"


@listener(r"hide.*", RE_NOPOST_COMMANG_FLAG)
def hide_roll(bot):
    """:love_letter: *hide roll*\n`/cc hide [PARAM|ANY_COMMENT]` """
    post_command("hide ？？？",
                 bot.token,
                 bot.data_user,
                 bot.channel_id,
                 bot.team_id,
                 bot.user_id)

    def post_hide(user_id):
        post_url = 'https://slack.com/api/chat.postMessage'
        state_data = get_state_data(bot.team_id, bot.user_id)
        user_param = get_user_param(bot.team_id, bot.user_id, state_data["pc_id"])
        channel = '@' + state_data["kp_id"]
        key = bot.key
        text = ""
        m = re.match(r"HIDE\s(.*?)(\+|\-|\*|\/)?(\d{,})?$", key)
        if m.group(1) not in user_param.keys():
            text = f"<@{user_id}> try talk"
            post_message = f"{key}"
            color = "gray"
        else:
            hide_message = "".join(['' if v is None else v for v in m.groups()])
            roll, operant, num_arg = analysis_roll_and_calculation(hide_message)

            alias_roll = {"こぶし": "こぶし（パンチ）"}
            if roll in alias_roll.keys():
                roll = alias_roll[roll]

            data = user_param[roll]

            num_rand = int(random.randint(1, 100))
            if roll.upper() in yig.config.LST_USER_STATUS_NAME:
                num = int(data)
            else:
                num = int(data[-1])

            num_targ = calculation(num, operant, num_arg)
            result, color = judge_1d100(num_targ, num_rand)
            raw_session_data = read_session_data(bot.team_id, "%s/%s.json" % (bot.channel_name ,state_data["pc_id"]))
            if raw_session_data:
                session_data = json.loads(raw_session_data)
                session_data.append({"roll": "hide " + roll.upper(),
                                     "num_targ": f"{num}{operant}{num_arg}",
                                     "num_rand": num_rand,
                                     "result": result})
                write_session_data(bot.team_id, "%s/%s.json" % (bot.channel_name ,state_data["pc_id"]), json.dumps(session_data, ensure_ascii=False))

            text = f"<@{user_id}> try {roll}"
            post_message = f"{result} 【{roll}】 {num_rand}/{num_targ} ({num}{operant}{num_arg})"

        payload = {
            'text': text,
            "attachments": json.dumps([
                {
                    "text": post_message,
                    "type": "mrkdwn",
                    "color": color
                }
            ])
        }
        post_result(bot.token,
                    user_id,
                    channel,
                    payload,
                    "gray")
    with futures.ThreadPoolExecutor() as executor:
        future_hide = executor.submit(post_hide, bot.user_id)
        future_hide.result()

    return_payload = {
        "text": "",
        "attachments": json.dumps([
            {
                "text": "【シークレットダイス】？？？",
                "type": "mrkdwn",
                "color": "gray"
            }])
    }

    return return_payload, "gray"


@listener("roll_skill", LAST_EVALUATION_FLAG)
def roll_skill(bot):
    state_data = get_state_data(bot.team_id, bot.user_id)
    user_param = get_user_param(bot.team_id, bot.user_id, state_data["pc_id"])
    roll, operant, num_arg = analysis_roll_and_calculation(bot.message)

    alias_roll = {"こぶし": "こぶし（パンチ）"}
    if roll in alias_roll.keys():
        roll = alias_roll[roll]

    if roll.upper() not in user_param:
        return f"{roll} その技能は覚えていません", "gray"
    data = user_param[roll.upper()]

    num_rand = int(random.randint(1, 100))
    if roll.upper() in yig.config.LST_USER_STATUS_NAME:
        num = int(data)
    else:
        num = int(data[-1])

    num_targ = calculation(num, operant, num_arg)
    result, color = judge_1d100(num_targ, num_rand)

    raw_session_data = read_session_data(bot.team_id, "%s/%s.json" % (bot.channel_name ,state_data["pc_id"]))
    if raw_session_data:
        session_data = json.loads(raw_session_data)
        session_data.append({"roll": roll.upper(),
                             "num_targ": f"{num}{operant}{num_arg}",
                             "num_rand": num_rand,
                             "result": result})
        write_session_data(bot.team_id, "%s/%s.json" % (bot.channel_name ,state_data["pc_id"]), json.dumps(session_data, ensure_ascii=False))

    now_hp, max_hp, now_mp, max_mp, now_san, max_san, db = get_basic_status(user_param, state_data)

    payload = {
        "attachments": json.dumps([{
            "thumb_url": get_pc_image_url(bot.team_id, bot.user_id, state_data["pc_id"], state_data["ts"]),
            "color": color,
            "footer": "<%s|%s>\nHP: *%s*/%s MP: *%s*/%s SAN: *%s*/%s DB: *%s*" % (user_param["url"], user_param["name"], now_hp, max_hp, now_mp, max_mp, now_san, max_san, db),
            "fields": [
                {
                    "value": "<@%s>" % (bot.user_id),
                    "type": "mrkdwn"
                },
                {
                    "title": f"*{result}* 【{roll}】 *{num_rand}*/{num_targ} ({num}{operant}{num_arg})",
                    "type": "mrkdwn"
                }
            ]
        }])}
    return payload, None


def get_sanc_result(cmd: str, pc_san: int) -> Tuple[str, str]:
    """
    Check SAN and return result message and color.
    Arguments:
        cmd {str} -- command text
        pc_san {int} -- PC's SAN value

    Returns:
        str -- report message
        str -- color that indicates success or failure
    """
    dice_result = int(random.randint(1, 100))
    is_success = pc_san >= dice_result
    if is_success:
        color = yig.config.COLOR_SUCCESS
        result_word = "成功"
    else:
        color = yig.config.COLOR_FAILURE
        result_word = "失敗"

    message = f"{result_word} 【SANチェック】 {dice_result}/{pc_san}"
    cmd_parts = cmd.split()
    if len(cmd_parts) == 2:
        match_result = split_alternative_roll_or_value(cmd_parts[1])
        if match_result:
            san_roll = match_result[0] if is_success else match_result[1]
            san_damage = sum(eval_roll_or_value(san_roll))
            message += f"\n【減少値】 {san_damage}"
    return message, color


def split_alternative_roll_or_value(cmd) -> Tuple[str, str]:
    """
    Split text 2 roll or value.
    Alternative roll is like following.
    - 0/1
    - 1/1D3
    - 1D20/1D100

    Arguments:
        cmd {str} -- command made by upper case
    Returns:
        tuple of 2 str or None
    """
    element_matcher = r"(\d+D?\d*)"
    result = re.fullmatch(f"{element_matcher}/{element_matcher}", cmd)
    if result is None or len(result.groups()) != 2:
        return None
    return result.groups()


def eval_roll_or_value(text: str) -> List[int]:
    """
    Evaluate text formated roll or value.
    If invalid format text is passed, just return [0].
    For dice roll, return values as list.
    Arguments:
        text {str} -- expect evaluatable text
                   examples: "1", "1D3", "2D6"
    Returns:
        List[int] -- evaluated values
    """
    try:
        return [int(text)]
    except ValueError:
        dice_matcher = re.fullmatch(r"(\d+)D(\d+)", text)
        if dice_matcher is None:
            return [0]
        match_numbers = dice_matcher.groups()
        dice_count = int(match_numbers[0])
        dice_type = int(match_numbers[1])
        if dice_count < 0 or dice_type < 0:
            return [0]
        return roll_dice(dice_count, dice_type)


def roll_dice(dice_count: int, dice_type: int) -> List[int]:
    """
    Get multiple and various dice roll result.
    ex) `roll_dice(2, 6)` means 2D6 and return each result like [2, 5].
    Arguments:
        dice_count {int} -- [description]
        dice_type {int} -- [description]
    Returns:
        List[int] -- All dice results
    """
    results = []
    for _ in range(dice_count):
        results.append(random.randint(1, dice_type))
    return results


def create_post_message_rolls_result(key: str) -> Tuple[str, str, int]:
    """
    Arguments:
        text {str} -- expect evaluatable text
                   examples: "1D3", "2D6", "2D6+3", "1D8+1D4"
    Returns:
        str -- post message
        str -- message detail
        str -- sum
    """
    str_message = ""
    sum_result = 0
    str_detail = ""
    cnt_ptr = 0
    for match in re.findall(r"\d+[dD]\d+", key):
        str_detail += f"{match}".ljust(80)
        is_plus = True
        if cnt_ptr > 0 and str(key[cnt_ptr - 1: cnt_ptr]) == "-":
            is_plus = False
        cnt_ptr += len(match) + 1
        roll_results = eval_roll_or_value(match)
        dice_sum = sum(roll_results)

        str_detail += ", ".join(map(str, roll_results))
        if is_plus:
            if str_message == "":
                str_message = match
            else:
                str_message += f"+{match}"
            sum_result += dice_sum
            str_detail += " [plus] \n"
        else:
            str_message += f"-{match}"
            sum_result -= dice_sum
            str_detail += " [minus] \n"

    if len(key) > cnt_ptr:
        is_plus = True
        if cnt_ptr > 0 and str(key[cnt_ptr - 1: cnt_ptr]) == "-":
            is_plus = False

        str_calc = key[cnt_ptr:]
        match = re.match(r"(\d+)", str_calc)
        result_now = int(match.group(1))

        if is_plus:
            str_message += f"+{str_calc}"
            sum_result += result_now
            str_detail += f"{result_now}".ljust(80)
            str_detail += f"{result_now} [plus] \n"
        else:
            str_message += f"-{str_calc}"
            sum_result -= result_now
            str_detail += f"{result_now}".ljust(80)
            str_detail += f"{result_now} [minus] \n"

    return str_message, str_detail, sum_result

def judge_1d100(target: int, dice: int):
    """
    Judge 1d100 dice result, and return text and color for message.
    Result is critical, success, failure or fumble.
    Arguments:
        target {int} -- target value (ex. skill value)
        dice {int} -- dice value
    Returns:
        message {string}
        rgb_color {string}
    """
    if dice <= target:
        if dice <= 5:
            return "クリティカル", yig.config.COLOR_CRITICAL
        return "成功", yig.config.COLOR_SUCCESS

    if dice >= 96:
        return "ファンブル", yig.config.COLOR_FUMBLE
    return "失敗", yig.config.COLOR_FAILURE


def analysis_roll_and_calculation(message:str) -> Tuple[str, str, int]:
    """
    Based on the given string, we analyze the object of the die
    and the supplementary formula.
    Arguments:
        message {str} -- target string (ex. DEX*5)
    Returns:
        roll {str}
        operant {str}
        number_argument {int}
    """
    proc = r"^(.*)(\+|\-|\*|\/)(\d+)$"
    result_parse = re.match(proc, message)
    operant = "+"
    number = 0
    if result_parse:
        roll = result_parse.group(1)
        operant = result_parse.group(2)
        number = int(result_parse.group(3))
    else:
        roll = message

    return roll, operant, number


def calculation(number_x:int, operant:str, number_y:int) -> int:
    """
    Perform a calculation from two values.
    Arguments:
        number_x {int} -- target int (ex. 30)
        operant  {str} -- target str (ex. +)
        number_y {int} -- target int (ex. 20)
    Returns:
        result_number {int}
    """
    if operant == '+':
        return number_x + number_y
    elif operant == '-':
        return number_x - number_y
    elif operant == '*':
        return number_x * number_y
    elif operant == '/':
        return math.ceil(number_x / number_y)
