from yig.bot import listener


@listener("SAVEIMG")
def save_image(bot):
    print("save image test")
    return "save image test", "#111111"
