from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()


@router.message(Command("promo"))
async def cmd_promo(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("🎁 Использование: <code>/promo КОД</code>", parse_mode="HTML")
        return
    code = parts[1].strip().upper()
    await message.answer(f"🎁 Промокод <code>{code}</code> принят.\n\n🚧 В разработке...", parse_mode="HTML") 
