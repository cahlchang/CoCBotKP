from yig.bot import listener

import yig.config
import random


@listener("景気づけ")
def keikiduke(bot):
    num = int(random.randint(1, 100))
    return f"景気づけ：{num}", yig.config.COLOR_ATTENTION


@listener("素振り")
def suburi(bot):
    random.seed()
    num = int(random.randint(1, 100))
    return f"素振り：{num}", yig.config.COLOR_ATTENTION


@listener("起床ガチャ")
def kisyo_gacha(bot):
    num = int(random.randint(1, 100))
    return f"起床ガチャ：{num}", yig.config.COLOR_ATTENTION


@listener("お祈り")
def oinori(bot):
    num = int(random.randint(1, 100))
    return f"お祈り：{num}", yig.config.COLOR_ATTENTION
