from typing import List, Tuple
import re
import json


from yig.bot import listener, RE_MATCH_FLAG, KEY_IN_FLAG
from yig.util import get_user_param, get_state_data ,set_state_data, get_status_message
import yig.config


@listener(("ステータス", "STATUS", "S"), KEY_IN_FLAG)
def show_status(bot):
    """status
    """
    dict_state = get_state_data(bot.team_id, bot.user_id)
    user_param = get_user_param(bot.team_id ,bot.user_id, dict_state["pc_id"])
    return get_status_message("STATUS", user_param, dict_state), yig.config.COLOR_ATTENTION


@listener("MEMO")
def show_memo(bot):
    """:pencil: *show user memo*
`/cc memo`
    """
    user_param = get_user_param(bot.team_id, bot.user_id)
    return user_param[bot.message], yig.config.COLOR_ATTENTION


@listener("GET")
def easteregg_dump_data(bot):
    """debug command
    """
    user_param = get_user_param(bot.team_id, bot.user_id)
    user_param.pop("memo")
    add_payload = {
        "text": "```" + json.dumps(user_param, ensure_ascii=False) + "```",
        "response_type": "ephemeral"
    }
    return add_payload, None


@listener(r"^(u+.*|update+.*)$", RE_MATCH_FLAG)
def update_user_status(bot):
    """:arrows_counterclockwise: *update user status*
`/cc u [ROLE][+-][POINT]`
`/cc update [ROLE][+-][POINT]`
    """
    result = analyze_update_command(bot.key)
    state_data = get_state_data(bot.team_id, bot.user_id)
    user_param = get_user_param(bot.team_id, bot.user_id, state_data["pc_id"])
    if result:
        status_name, operator, arg = result
        if status_name in state_data:
            val_targ = state_data[status_name]
        else:
            val_targ = "0"

        num_targ = eval(f'{val_targ}{operator}{arg}')
        state_data[status_name] = num_targ
        set_state_data(bot.team_id, bot.user_id, state_data)
    return get_status_message("UPDATE STATUS", user_param, state_data), yig.config.COLOR_ATTENTION


def analyze_update_command(command: str) -> Tuple[str, str, str]:
    """
    analyze update command and return status name, operator and arg

    Arguments:
        command {str} -- command text

    Returns:
        str -- status_name
        str -- operator
        str -- arg

    Examples:
        "u MP+1" => ("MP", "+", "1")
        "u SAN - 10" => ("SAN", "-", "10")
    """
    result = re.fullmatch(r"(.+)\s+(\S+)\s*(\+|\-|\*|\/)\s*(\d+)$", command)
    if result is None:
        return None
    return result.group(2), result.group(3), result.group(4)

