from yig.bot import listener

import yig.config
import random


@listener("景気づけ")
def easteregg_keikiduke(bot):
    """toy_1
    """
    num = int(random.randint(1, 100))
    return f"景気づけ：{num}", yig.config.COLOR_ATTENTION


@listener("素振り")
def easteregg_suburi(bot):
    """toy_2
    """
    random.seed()
    num = int(random.randint(1, 100))
    return f"素振り：{num}", yig.config.COLOR_ATTENTION


@listener("起床ガチャ")
def easteregg_kisyo_gacha(bot):
    """toy_3
    """
    num = int(random.randint(1, 100))
    return f"起床ガチャ：{num}", yig.config.COLOR_ATTENTION


@listener("お祈り")
def easteregg_oinori(bot):
    """toy_4
    """
    num = int(random.randint(1, 100))
    return f"お祈り：{num}", yig.config.COLOR_ATTENTION
