import re

from aiogram import Router, types, F
from aiogram.filters import Command, CommandObject
from aiogram.utils.i18n import gettext as _
from magic_filter import RegexpMode

from bot_app.application import SubscriptionService
from bot_app.modules.dynamic_page_channels_browser import DynamicPageChannelsBrowser
from shared.telegram.callbacks.subscribe import SubscribeAndUpdateBrowserData

subscribe_router = Router()


MENTION_BY_USERNAME_REGEXP = re.compile(r'\s*@([a-zA-z\d_]+)\s*')


@subscribe_router.message(Command(commands=[re.compile(r'sub_(\d+)')]))
async def subscribe(
    message: types.Message,
    command: CommandObject,
    subscription_service: SubscriptionService,
):
    channel_shifted_id = int(command.regexp_match.groups()[0])

    if not (channel_username := await subscription_service.get_channel_username_by_id(channel_shifted_id)):
        await message.answer(_('channel_not_found_by_shifted_id'))
        return

    await subscription_service.subscribe_to_known_channel_by_username(message.from_user.id, channel_username)

    await message.answer(_('successful_subscribe {channel_title}').format(channel_title=channel_username))


@subscribe_router.callback_query(SubscribeAndUpdateBrowserData.filter())
async def subscribe_and_update_browser(
    callback: types.CallbackQuery,
    callback_data: SubscribeAndUpdateBrowserData,
    subscription_service: SubscriptionService,
):
    if not (channel_username := await subscription_service.get_channel_username_by_id(callback_data.channel_id)):
        await callback.message.answer(_('channel_not_found_by_shifted_id'))
        return

    await subscription_service.subscribe_to_known_channel_by_username(callback.from_user.id, channel_username)

    try:
        await DynamicPageChannelsBrowser.send(
            callback.message.edit_text,
            callback.from_user.id,
            offset=callback_data.current_offset,
        )
    finally:
        await callback.answer(_('successful_subscribed_to {channel_username}').format(channel_username=channel_username))


@subscribe_router.message(F.text.regexp(MENTION_BY_USERNAME_REGEXP, mode=RegexpMode.FULLMATCH))
async def subscribe_by_username(message: types.Message, subscription_service: SubscriptionService):
    channel_username = MENTION_BY_USERNAME_REGEXP.fullmatch(message.text).groups()[0]

    await subscription_service.subscribe_to_channel_by_username(message.from_user.id, channel_username)

    await message.answer(_('successful_subscribe {channel_title}').format(channel_title=channel_username))
