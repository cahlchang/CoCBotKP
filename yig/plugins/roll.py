import re
import random
import math
from typing import List, Tuple
from concurrent import futures

from yig.bot import listener, RE_MATCH_FLAG, RE_NOPOST_COMMANG_FLAG, LAST_EVALUATION_FLAG
from yig.util import get_user_param, get_state_data ,set_state_data, get_status_message
import yig.config


@listener(r"sanc.*", RE_MATCH_FLAG)
def sanity_check(bot):
    # post_command(message, token, data_user, channel_id)
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
def hide_roll(bot):
    str_message, str_detail, sum_result = create_post_message_rolls_result(bot.key)
    return f"*{sum_result}* 【ROLLED】\n {str_detail}", "#4169e1"


@listener(r"hide.*", RE_NOPOST_COMMANG_FLAG)
def hide_roll(bot):
    post_command("hide ？？？",
                 bot.token,
                 bot.data_user,
                 bot.channel_id)
    text = "結果は公開されず、KPが描写だけ行います"

    payload = {
        'text': text,
        "attachments": json.dumps([
            {
                "text": return_message,
                "type": "mrkdwn",
                "color": color
            }
        ])
    }

    res = requests.post(bot.response_url,
                        data=json.dumps(payload),
                        headers={'Content-Type': 'application/json'})
    print(res.text)

    def post_hide(user_id):
        post_url = 'https://slack.com/api/chat.postMessage'
        dict_state = get_state_data(bot.team_id, bot.user_id)
        param = get_user_param(bot.team_id, bot.user_id, dict_state["pc_id"])
        channel = '@' + dict_state["kp_id"]
        color_hide = "gray"

        m = re.match(r"HIDE\s(.*?)(\+|\-|\*|\/)?(\d{,})?$", key)
        if m is None:
            text = "role not found"
            post_message = f"技能名が解釈できません。\n{key}"
        elif m.group(1) and m.group(1) not in param:
            text = "role miss"
            name_role = m.group(1)
            post_message = f"この技能は所持していません。\n{key}"
        else:
            name_role = m.group(1)
            n_targ = 0
            msg_rev = "+0"
            if type(param[name_role]) == list:
                n_targ = int(param[name_role][5])
            else:
                n_targ = int(param[name_role])

            msg_disp = n_targ

            if name_role in dict_state:
                n_targ += dict_state[name_role]
            if m.group(2) is not None:
                if m.group(2) == "+":
                    n_targ += int(m.group(3))
                    msg_rev = "+" + str(m.group(3))
                elif m.group(2) == "-":
                    n_targ -= int(m.group(3))
                    msg_rev = "-" + str(m.group(3))
                elif m.group(2) == "*":
                    n_targ *= int(m.group(3))
                    msg_rev = "*" + str(m.group(3))
                elif m.group(2) == "/":
                    n_targ /= int(m.group(3))
                    msg_rev = "/" + str(m.group(3))

            num = int(random.randint(1, 100))

            str_result, color_hide = judge_1d100(int(n_targ), num)
            post_message = f"{str_result} 【{name_role}】 {num}/{n_targ} ({msg_disp}{msg_rev})"
            text = f"<@{user_id}> try {name_role}"

        payload = {
            'token': token,
            'channel': channel,
            'text': text,
            "attachments": json.dumps([
                {
                    "text": post_message,
                    "type": "mrkdwn",
                    "color": "gray"
                }
            ])
        }

        res = requests.post(post_url, data=payload)
    with futures.ThreadPoolExecutor() as executor:
        future_hide = executor.submit(post_hide, user_id)
        future_hide.result()

    return "【シークレットダイス】？？？", "gray"


@listener("roll_skill", LAST_EVALUATION_FLAG)
def roll_skill(bot):
    user_param = get_user_param(bot.team_id, bot.user_id)

    lst_trigger_status = ["知識",
                          "アイデア",
                          "幸運",
                          "STR",
                          "CON",
                          "POW",
                          "DEX",
                          "APP",
                          "SIZ",
                          "INT",
                          "EDU",
                          "HP",
                          "MP"]

    proc = r"^(.*)(\+|\-|\*|\/)(\d+)$"

    result_parse = re.match(proc, bot.message)
    is_correction = False
    msg_correction = "+0"
    if result_parse:
        bot.message = result_parse.group(1)
        operant = result_parse.group(2)
        args = result_parse.group(3)
        msg_correction = operant + args
        is_correction = True

    alias_roll = {"こぶし": "こぶし（パンチ）"}

    if bot.message in alias_roll.keys():
        bot.message = alias_roll[bot.message]

    data = user_param[bot.message]

    num = int(random.randint(1, 100))
    if "現在SAN" == bot.message or bot.message.upper() in lst_trigger_status:
        num_targ = data
    else:
        num_targ = data[-1]

    msg_num_targ = num_targ
    if is_correction:
        num_targ = eval('{}{}{}'.format(num_targ, operant, args))
        num_targ = math.ceil(num_targ)

    str_result, color = judge_1d100(int(num_targ), num)
    message = bot.message
    return f"{str_result} 【{message}】 {num}/{num_targ} ({msg_num_targ}{msg_correction})", color


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
    """"
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
