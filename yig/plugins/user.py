from yig.bot import listener, RE_MATCH_FLAG
from yig.util import get_user_param

import yig.config


@listener("memo")
def show_params(bot):
    """:pencil: *show user memo*
`/cc memo`
    """
    user_param = get_user_param(bot.user_id)
    return user_param[bot.message], yig.config.COLOR_ATTENTION

