from aiogram import F, Router, types
from aiogram.utils.i18n import lazy_gettext as __

from bot_app.modules.dynamic_page_channels_browser import DynamicPageChannelsBrowser
from shared.telegram.callbacks.channel_browser import ChannelsBrowserNavigationData

channels_browser_router = Router()


@channels_browser_router.message(F.text == __('channels_browser'))
async def channels_browser_handler(message: types.Message):
    await DynamicPageChannelsBrowser.send(
        message.answer,
        message.from_user.id,
    )


@channels_browser_router.callback_query(ChannelsBrowserNavigationData.filter())
async def channels_browser_scroll_handler(
    callback: types.CallbackQuery,
    callback_data: ChannelsBrowserNavigationData
):
    await DynamicPageChannelsBrowser.send(
        callback.message.edit_text,
        callback.from_user.id,
        offset=callback_data.new_offset,
    )

    await callback.answer()
