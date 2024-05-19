from aiogram import Router, types, F, Bot
from aiogram.enums.parse_mode import ParseMode
from aiogram.filters import Command
from aiogram.utils.i18n import gettext as _, lazy_gettext as __

from bot_app.application import SubscriptionService, PackService
from bot_app.tg.keyboards.search import search_kb
from bot_app.tg.keyboards.packs import packs_list_kb, pack_kb

from shared.telegram.callbacks.packs import PackNavigation, PackData, PackSubscribeData, PackToList


search_router = Router()


@search_router.message(F.text == __('search_submenu'))
async def full_search_menu(message: types.Message):
    await message.answer(text=_('search_submenu_text'), reply_markup=search_kb())


@search_router.message(Command(commands=['search']))
@search_router.message(F.text == __('channels_search'))
async def search_menu(message: types.Message):
    await message.answer(
        text=_('start_search_tip'),
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[[
                types.InlineKeyboardButton(text=_('start_search_button'), switch_inline_query_current_chat='\n'*20),
            ]],
        ),
    )


@search_router.inline_query(F.chat_type == 'sender')
async def search(
    inline_query: types.InlineQuery,
    subscription_service: SubscriptionService,
):
    q = inline_query.query.strip()
    channels = await subscription_service.get_channels(q)
    if not channels:
        await inline_query.answer([])
        return
        # await inline_query.answer(
        #     [types.InlineQueryResultArticle(
        #         id=inline_query.from_user.username,
        #         title='Не нашлось ни одного канала 😔',
        #         input_message_content=types.InputTextMessageContent(
        #             message_text='/search',
        #             disable_web_page_preview=True,
        #             parse_mode=ParseMode.HTML,
        #         ),
        #     ),
        #     ],
        # )
    response = []
    for channel in channels:
        photo = f'https://s3.timeweb.com/1f01a77b-ai-open-news/channel_thumbnails/{channel.username}.jpg'

        description = channel.description.split('\n')[0] if channel.description else ''
        description = description[:32] + '...'
        description += '\n'
        # description += f'{channel.member_count} подписчиков'
        description += _('subscribers_count {count}').format(count=channel.member_count)

        msg_text = ''
        # msg_text += hide_link(photo)
        msg_text += channel.title
        msg_text += '\n'
        msg_text += '@' + channel.username
        msg_text += '\n\n'
        # msg_text += f'{channel.member_count} подписчиков'
        msg_text += _('subscribers_count {count}').format(count=channel.member_count)
        if channel.description:
            msg_text += '\n\n'
            msg_text += channel.description
        sub_button = types.InlineKeyboardButton(
            text=_('search_subscribe_button'),
            callback_data=f'subscribe:{inline_query.from_user.id}:{channel.username}',
            )
        back_button = types.InlineKeyboardButton(
            text=_('search_back_to_search_button'),
            switch_inline_query_current_chat=inline_query.query,
            )
        response.append(
            types.InlineQueryResultArticle(
                id=channel.username,
                title=channel.title,
                description=description,
                input_message_content=types.InputTextMessageContent(
                    message_text=msg_text,
                    disable_web_page_preview=True,
                    parse_mode=ParseMode.HTML,
                ),
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[sub_button], [back_button]]),
                thumbnail_url=photo,
            ),
        )
    await inline_query.answer(response, is_personal=True)


@search_router.callback_query(F.data.startswith('subscribe:'))
async def subscribe(
    call: types.CallbackQuery,
    bot: Bot,
    subscription_service: SubscriptionService,
):
    await call.answer()
    prefix, user_id, channel_username = call.data.split(':')
    await subscription_service.subscribe_to_known_channel_by_username(int(user_id), channel_username)
    # text = 'Вы подписались на @' + channel_username
    text = _('subscribed_from_search {channel_username}').format(channel_username=channel_username)
    await bot.send_message(user_id, text, disable_web_page_preview=True)


@search_router.message(F.text == __('channel_packs'))
async def show_channel_packs(message: types.Message, pack_service: PackService):
    packs = await pack_service.get_some_packs()
    text = _('available_packs')
    markup = packs_list_kb(packs)
    await message.answer(text=text, reply_markup=markup)


@search_router.callback_query(PackData.filter())
async def select_pack(callback: types.CallbackQuery, callback_data: PackData, pack_service: PackService):
    pack = await pack_service.get_pack_channels(pack_id=callback_data.id)
    text = pack.name
    text += '\n\n'
    for channel in pack.channels:
        text += f'@{channel.username} {channel.title}\n'
    markup = pack_kb(callback_data.id, callback_data.offset, callback_data.limit)
    await callback.message.edit_text(text=text, reply_markup=markup)


@search_router.callback_query(PackSubscribeData.filter())
async def pack_subscribe(
    callback: types.CallbackQuery,
    callback_data: PackSubscribeData,
    pack_service: PackService,
    subscription_service: SubscriptionService,
):
    await callback.answer()
    pack = await pack_service.get_pack_channels(pack_id=callback_data.id)
    for channel in pack.channels:
        await subscription_service.subscribe_to_known_channel_by_username(callback.from_user.id, channel.username)
    await callback.message.answer(_('pack_subscribed'))


@search_router.callback_query(PackToList.filter())
async def pack_back_to_list(callback: types.CallbackQuery, callback_data: PackToList, pack_service: PackService):
    packs = await pack_service.get_some_packs(offset=callback_data.offset, limit=callback_data.limit)
    text = _('available_packs')
    markup = packs_list_kb(packs, offset=callback_data.offset, limit=callback_data.limit)
    await callback.message.edit_text(text=text, reply_markup=markup)


@search_router.callback_query(PackNavigation.filter())
async def pack_navigation(callback: types.CallbackQuery, callback_data: PackToList, pack_service: PackService):
    packs = await pack_service.get_some_packs(offset=callback_data.offset, limit=callback_data.limit)
    if not packs:
        return await callback.answer()
    text = _('available_packs')
    markup = packs_list_kb(packs, offset=callback_data.offset, limit=callback_data.limit)
    await callback.message.edit_text(text=text, reply_markup=markup)
