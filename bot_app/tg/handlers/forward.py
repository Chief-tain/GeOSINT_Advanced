from aiogram import Bot, F, Router, types
from aiogram.exceptions import TelegramAPIError
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _

from bot_app.application import SubscriptionService

forward_router = Router()


@forward_router.message(
    F.forward_from_chat & F.forward_from_chat.type == 'channel'
)
async def subscribe(
    message: types.Message,
    bot: Bot,
    state: FSMContext,
    subscription_service: SubscriptionService
):
    try:
        channel_info = await bot.get_chat(message.forward_from_chat.id)
    except TelegramAPIError:
        await message.answer(_('channel_is_private'))
        return
    # subscription_count = len(await subscription_service.get_subscriptions(message.from_user.id))
    # data = await state.get_data()
    # premium = data.get('premium')
    # if (premium == -1) and (subscription_count >= 3):
    #     text = 'Для подписки на большее число каналов необходима подписка Silver или Gold.\n'
    #     text += 'Сменить тариф можно в Настройки -> Подписка'
    #     await message.answer(text)
    #     return
    # if (premium == 0) and (subscription_count >= 15):
    #     text = 'Для подписки на большее число каналов необходима подписка Gold.\n'
    #     text += 'Сменить тариф можно в Настройки -> Подписка'
    #     await message.answer(text)
    #     return
    # if (premium == 100) and (subscription_count >= 200):
    #     text = 'В данный момент нельзя подписаться больше, чем на 200 каналов.'
    #     await message.answer(text)
    #     return
    member_count = await channel_info.get_member_count()
    await subscription_service.subscribe_to_channel_with_known_info(
        user_id=message.from_user.id,
        channel_shifted_id=channel_info.shifted_id,
        channel_title=channel_info.title,
        channel_description=channel_info.description,
        channel_username=channel_info.username,
        channel_member_count=member_count,
    )

    text = _('successful_subscribe {channel_title}')
    text = text.format(channel_title=channel_info.title)
    await message.answer(text)


@forward_router.message(F.chat_shared)
async def process_shared_channel(
    message: types.Message,
    subscription_service: SubscriptionService
):
    channel_id = message.chat_shared.chat_id
    short_id = str(channel_id).replace("-100", "")
    shift = int(-1 * pow(10, len(short_id) + 2))
    shifted_id = shift - channel_id
    channel_title = await subscription_service.get_channel_username_by_shifted_id(shifted_id)
    if not channel_title:
        await message.answer(_('unknown_channel'))
    else:
        await subscription_service.subscribe_to_known_channel_by_username(int(message.from_user.id), channel_title)
        text = _('successful_subscribed_to {channel_username}')
        text = text.format(channel_username=channel_title)
        await message.answer(text)
