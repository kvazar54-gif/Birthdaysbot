from aiogram.filters import CommandStart
from aiogram import F, Router
from aiogram.types import Message
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import datetime


import app.keyboards as kb
import app.database.requests as rq


router = Router()

class Celebrant(StatesGroup):
    name = State()
    date = State()
    del_name = State()


@router.message(CommandStart())
async def cmd_start(message: Message):
    await rq.set_user(message.from_user.id)
    await message.answer('Привет! Я бот для создания напоминаний о днях рождения.',
                    reply_markup=kb.main)


@router.message(F.text=='Добавить имениннника 🎂')
async def name_request(message: Message, state: FSMContext):
    await state.set_state(Celebrant.name)
    await message.answer('Введите имя именинника (длиной от 2 до 25 символов)')


@router.message(Celebrant.name)
async def adding_name(message: Message, state: FSMContext):
    if 2 <= len(message.text) <= 25:
        await state.update_data(name=message.text)
        await state.set_state(Celebrant.date)
        await message.answer('Введите дату рождения в формате ДД.ММ')
    else:
        await message.answer("❌ Ошибка! Имя должно быть от 2 до 25 символов. Попробуйте еще раз:")


@router.message(Celebrant.date)
async def adding_date(message: Message, state: FSMContext):
    try:
        day_month = datetime.datetime.strptime(message.text, "%d.%m")
        day_month = day_month.replace(year=2024)
    except ValueError:
        await message.answer("❌ Ошибка! Введите дату в формате ДД.ММ (например, 16.01)")
        return
    
    await state.update_data(user_date=day_month)
    data = await state.get_data()

    all_celebrants = await rq.get_celebrants(message.from_user.id)
    existing_names = [celebrant['name'] for celebrant in all_celebrants]
    
    if data['name'] in existing_names:
        await message.answer(
            f"❌ Именинник с именем '{data['name']}' уже существует!\n"
            f"Пожалуйста, используйте другое имя или удалите существующего именинника."
        )
        await state.clear()
        return
    
    await rq.adding_celebrant(message.from_user.id, data['name'], day_month.strftime('%Y-%m-%d'))
    await message.answer(f"✅ Именинник добавлен!\nИмя: {data['name']}\nДата рождения: {day_month.strftime('%d.%m')}")
    await state.clear()


@router.message(F.text=='Список имениннников 📋')
async def show_celebrants(message: Message):
    user_id = message.from_user.id
    all_celebrants = await rq.get_celebrants(user_id)
    
    if not all_celebrants:
        await message.answer("📭 Вы еще никого не записали.")
        return
    
    table_text = f" {'Имя':<25}   {'Дата':<5}\n"
    table_text += "-" * 33 + "\n"
    
    for celebrant in all_celebrants:
        date_parts = celebrant['event_date'].split('-')
        day_month = f"{date_parts[2]}.{date_parts[1]}"
        table_text += f" {celebrant['name']:<25} | {day_month:<5}\n"
    
    await message.answer(f"📋 Именинники:\n\n<pre>{table_text}</pre>", parse_mode="HTML")


@router.message(F.text=='Удалить имениннника ❌')
async def del_request(message: Message, state: FSMContext):
    user_id = message.from_user.id
    all_celebrants = await rq.get_celebrants(user_id)
    
    if not all_celebrants:
        await message.answer("📭 У вас нет именинников для удаления.")
        return
    
    # Показываем список
    table_text = f" {'Имя':<25}   {'Дата':<5}\n"
    table_text += "-" * 33 + "\n"
    
    for celebrant in all_celebrants:
        date_parts = celebrant['event_date'].split('-')
        day_month = f"{date_parts[2]}.{date_parts[1]}"
        table_text += f" {celebrant['name']:<25} | {day_month:<5}\n"
    
    await message.answer(
        f"Ваши именинники:\n\n<pre>{table_text}</pre>\n\n"
        f"Введите имя именинника для удаления:",
        parse_mode="HTML"
    )
    await state.set_state(Celebrant.del_name)


@router.message(Celebrant.del_name)
async def del_name(message: Message, state: FSMContext):
    user_id = message.from_user.id
    name_to_delete = message.text.strip()

    all_celebrants = await rq.get_celebrants(user_id)

    found = None
    for celebrant in all_celebrants:
        if celebrant['name'] == name_to_delete:
            found = celebrant
            break
    
    if found:
        await rq.delete_celebrant(user_id, name_to_delete)
        
        date_parts = found['event_date'].split('-')
        day_month = f"{date_parts[2]}.{date_parts[1]}"
        
        await message.answer(
            f"✅ Именинник удалён!\n"
            f"Имя: {name_to_delete}\n"
            f"Дата: {day_month}"
        )
    else:
        await message.answer(
            f"❌ Именинник '{name_to_delete}' не найден.\n"
            f"Проверьте правильность написания."
        )
    
    await state.clear()
