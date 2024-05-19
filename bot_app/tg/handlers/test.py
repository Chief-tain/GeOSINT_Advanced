from aiogram import F, Router, types


test_router = Router()


@test_router.message(F.text)
async def test_router_func(
    message: types.Message,
):
    await message.answer(message.text)
