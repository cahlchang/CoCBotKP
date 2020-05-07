import requests

from yig.bot import listener
from yig.util import get_state_data


@listener("SAVEIMG")
def save_image(bot):
    """
    This function saves the slack icon image to S3.
    """
    print("save image test")
    state_data = get_state_data(bot.user_id)
    icon_url = bot.data_user["profile"]["image_1024"]
    response = requests.get(icon_url)
    content_type = response.headers["content-type"]
    if 'image' not in content_type:
        exception = Exception("Content-Type: " + content_type)
        raise exception

    image_content = response.content
    filename = "%s/%s" % (bot.user_id, state_data["pc_id"])
    with open(filename, "wb") as fout:
        fout.write(image_content)

    return "save image ok", "#111111"
