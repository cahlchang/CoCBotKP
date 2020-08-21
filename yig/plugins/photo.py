import requests


from yig.bot import listener
from yig.util.data import get_state_data
from yig.util.view import write_pc_image, get_charaimage
import yig.config


@listener("SAVEIMG")
def icon_save_image(bot):
    """:art: *save slack icon*\n`/cc saveimg`"""
    state_data = get_state_data(bot.team_id, bot.user_id)
    icon_url = bot.data_user["profile"]["image_512"]
    image_path = write_pc_image(bot.team_id, bot.user_id, state_data["pc_id"], icon_url)
    return "アイコンを保存しました。", yig.config.COLOR_ATTENTION


@listener("LOADIMG")
def icon_load_image(bot):
    """:frame_with_picture: *load icon image*\n`/cc loadimg`"""
    state_data = get_state_data(bot.team_id, bot.user_id)
    image = get_charaimage(bot.team_id, bot.user_id, state_data["pc_id"])
    param = {
        'token': bot.token,
        "channels": bot.channel_id
    }
    res = requests.post(url="https://slack.com/api/files.upload",
                        params=param,
                        files={'files': image})

    return "アイコン画像をロードしました。", yig.config.COLOR_ATTENTION
