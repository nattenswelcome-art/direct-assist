from aiogram.utils.keyboard import ReplyKeyboardBuilder

def get_main_kb():
    builder = ReplyKeyboardBuilder()
    builder.button(text="Собрать семантику")
    builder.button(text="Генерация из списка")
    builder.button(text="Анализ сайта")
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)
