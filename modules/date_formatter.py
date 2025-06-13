def translate_date(time_delta: str, user_id: int, bot):
    return time_delta.replace("days", bot.get_text(user_id, "days")).replace("day", bot.get_text(user_id, "day"))
