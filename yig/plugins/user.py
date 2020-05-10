from yig.bot import listener, RE_MATCH_FLAG
from yig.util import get_user_param

import yig.config

@listener(r"(DB|memo)", RE_MATCH_FLAG)
def show_params(bot):
    """
    show_params function is PC parameter from AWS S3
    """
    user_param = get_user_param(bot.user_id)
    return user_param[bot.message], yig.config.COLOR_ATTENTION

