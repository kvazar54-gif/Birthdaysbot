from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


main = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Добавить имениннника 🎂')],
        [KeyboardButton(text='Список имениннников 📋')],
        [KeyboardButton(text='Удалить имениннника ❌')],
    ],
    resize_keyboard=True,
    input_field_placeholder='Выберите пункт меню'
)
