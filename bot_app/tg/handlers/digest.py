import asyncio
import logging
from collections import Counter
from math import ceil
from datetime import datetime

from aiogram import F, Router, types, flags, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import LinkPreviewOptions, BufferedInputFile
from aiogram.utils.chat_action import ChatActionSender
from aiogram.utils.i18n import gettext as _, lazy_gettext as __
from aiogram.exceptions import TelegramForbiddenError, TelegramAPIError, TelegramRetryAfter, TelegramBadRequest
from sqlalchemy.ext.asyncio import AsyncSession

from bot_app.application import RabbitService
from bot_app.application.advertisement.service import AdsService
from bot_app.application.hasgtags import HashtagApp
from bot_app.application.kb_query_tool.kb_query_tool import KbQueryTool
from bot_app.application.web_search.service import WebSearchChatGPTService
from bot_app.tg.filters.deep_links import StrictDeeplink
from bot_app.tg.helpers import follow_min_timestamp_callback
from bot_app.tg.keyboards.digest import expanded_search_kb
from bot_app.application.hasgtags.lang_names import language_names
from bot_app.modules.direct_message_editing import direct_message_editing, td_manipulations, get_buttons_and_objects
from shared import settings
from shared.dbs.db_gateway_async import DatabaseGatewayAsync
from shared.digest import TextDigest
from shared.settings import TAG_PROMT_STYLING
from shared.telegram.callbacks.digest import AdvertisementData, DigestNavigationData, DigestToVoice, CategorylData, \
    GetFullDigest, CategoryPaginationPrevious, ShowCategories, CategoryPaginationNext, ExpandedSearchData
from shared.voice.summary import SummaryTTSUploader
from shared.voice.voice_gluer import VoiceGluer
from shared.categories_classes import categories_classes

MIN_LENGTH_QUERY = 5

digest_router = Router()


@digest_router.message(
    StrictDeeplink(deep_link=True, deep_link_encoded=False),
    flags={
        "enable_sequential_request": True,
        "key_sequential_request": "web_search"
    })
async def change_hashtag(
    message: types.Message,
    rabbit_service: RabbitService,
    kb_query_tool: KbQueryTool,
    hashtag_app: HashtagApp,
    bot: Bot,
):
    try:
        deeplink_params = message.text.split()[1]
        deeplink_params = deeplink_params.split('_')
        user_id = message.from_user.id

        await message.delete()

        if len(deeplink_params) == 2:
            
            async with ChatActionSender.typing(bot=message.bot, chat_id=message.chat.id):
                openning_message = await message.answer(_('openning_message'))
                
                data, links, language = await hashtag_app.search_by_hashtags(summary_id=int(deeplink_params[1]))
                article = await hashtag_app.get_text_by_summary_id(summary_id=int(deeplink_params[1]))

                logging.info(f'Language: {language_names[language]}')
                logging.info(f'Start tag search with: {data}')
                logging.info(f'Links for tag search: {links}')
                logging.info(f'Text for tag search: {article}')
                
                response = await WebSearchChatGPTService(  # NOQA
                    openning_message,
                    model='gpt-3.5-turbo-0125'
                )._process_chat_completions(
                    article,
                    promt_styling=TAG_PROMT_STYLING.format(article=article, news=data, language=language_names[language])
                )
                
                response = response.choices[0].message.content
                
                response += f'\n\n Источники: {links}'
                
                await openning_message.delete()
                await message.answer(response, reply_markup=expanded_search_kb(summary_id=int(deeplink_params[1])))
                
        else:
            reaction = deeplink_params[0]
            summary_id = int(deeplink_params[1])
            digest_id = int(deeplink_params[2])
            offset = int(deeplink_params[3])
            current_category = int(deeplink_params[4])

            await hashtag_app.main_reaction_func(
                user_id=user_id,
                summary_id=summary_id,
                current_reaction=reaction
                )

            await rabbit_service.edit_digest_offset_command(
                user_id=user_id,
                bot_id=bot.id,
                digest_id=digest_id,
                offset=offset,
                message_id=await kb_query_tool.get_message_id_by_digest_id(digest_id=digest_id),
                category=current_category
            )

    except Exception as error:  # NOQA
        raise        


@digest_router.callback_query(ExpandedSearchData.filter())
async def expanded_search(
    callback: types.CallbackQuery,
    callback_data: ExpandedSearchData,
    hashtag_app: HashtagApp
):
    await callback.answer()
    await callback.message.edit_reply_markup()
    
    summary_text = await hashtag_app.get_text_by_summary_id(summary_id=callback_data.summary_id)

    if len(summary_text) <= MIN_LENGTH_QUERY:
        await callback.message.answer(_('web_search_failed_short_query'))
        return True

    async with ChatActionSender.typing(bot=callback.bot, chat_id=callback.message.chat.id):
        openning_message = await callback.message.answer(_('openning_message'))
        response = await WebSearchChatGPTService(openning_message).search(summary_text)
        await openning_message.delete()
        await callback.message.answer(response)
    
    
@digest_router.callback_query(DigestNavigationData.filter())
@follow_min_timestamp_callback()
async def render_digest(
    callback: types.CallbackQuery,
    callback_data: DigestNavigationData,
    rabbit_service: RabbitService,
    bot: Bot,
):

    await callback.answer()
    await rabbit_service.edit_digest_offset_command(
        user_id=callback.from_user.id,
        bot_id=bot.id,
        digest_id=callback_data.digest_id,
        offset=callback_data.new_offset,
        message_id=callback.message.message_id,
        category=callback_data.category,
        with_subscribe_suggestions=callback_data.with_subscribe_suggestions,
    )


@digest_router.callback_query(CategorylData.filter())  # , Premium(PremiumLevel.SILVER, "Фильтр по категориям"))
async def render_digest_by_category(
    callback: types.CallbackQuery,
    callback_data: CategorylData,
    bot: Bot,
    state: FSMContext,
    db_gateway: DatabaseGatewayAsync,
    kb_query_tool: KbQueryTool,
):
    await callback.answer()
    user_data = await state.get_data()
    language_code = user_data.get('locale', 'en')
    digest = await db_gateway.get_digest(callback_data.digest_id)
    keyboard_position = await kb_query_tool.get_kb_position(message_id=callback.message.message_id)
    show_category_keyboard = await kb_query_tool.get_show_kb_value(message_id=callback.message.message_id)
        
    text_digest = await td_manipulations(
        digest=digest,
        category=callback_data.category,
        user_id=callback.from_user.id,
        keyboard_position=keyboard_position,
        show_category_keyboard=show_category_keyboard,
        language_code=language_code
        )
        
    await direct_message_editing(
        text_digest=text_digest,
        bot=bot,
        user_id=callback.from_user.id,
        message_id=callback.message.message_id,
        link_preview_options=callback.message.link_preview_options
    )
    

@digest_router.callback_query(GetFullDigest.filter())
async def get_full_digest(
    callback: types.CallbackQuery,
    callback_data: GetFullDigest,
    kb_query_tool: KbQueryTool,
    bot: Bot,
    db_gateway: DatabaseGatewayAsync,
    state: FSMContext,
):
    await callback.answer()
    
    user_data = await state.get_data()
    language_code = user_data.get('locale', 'en')
    digest = await db_gateway.get_digest(callback_data.digest_id)
    await kb_query_tool.reset_kb_position(message_id=callback.message.message_id)
    
    text_digest = await td_manipulations(
        digest=digest,
        user_id=callback.from_user.id,
        show_category_keyboard=True,
        language_code=language_code
        )
    
    await direct_message_editing(
        text_digest=text_digest,
        bot=bot,
        user_id=callback.from_user.id,
        message_id=callback.message.message_id,
        link_preview_options=callback.message.link_preview_options
    )


@digest_router.callback_query(CategoryPaginationNext.filter())
async def render_digest_keyboard(
    callback: types.CallbackQuery,
    callback_data: CategoryPaginationNext,
    rabbit_service: RabbitService,
    kb_query_tool: KbQueryTool,
    bot: Bot,
):
    await kb_query_tool.change_kb_position(
        message_id=callback.message.message_id,
        direction='next',
        category_pages=callback_data.category_pages
        )

    await callback.answer()
    await rabbit_service.change_digest_keyboard(
        user_id=callback.from_user.id,
        bot_id=bot.id,
        digest_id=callback_data.digest_id,
        offset=callback_data.new_offset,
        message_id=callback.message.message_id,
        with_subscribe_suggestions=callback_data.with_subscribe_suggestions,
    )


@digest_router.callback_query(ShowCategories.filter())  # , Premium(PremiumLevel.SILVER, "Фильтр по категориям"))
async def render_digest_keyboard(
    callback: types.CallbackQuery,
    callback_data: ShowCategories,
    state: FSMContext,
    kb_query_tool: KbQueryTool,
    db_gateway: DatabaseGatewayAsync,
):
    await callback.answer()
    
    user_data = await state.get_data()
    language_code = user_data.get('locale', 'en')
    await kb_query_tool.change_show_kb_value(message_id=callback.message.message_id)
    show_category_keyboard = await kb_query_tool.get_show_kb_value(message_id=callback.message.message_id)
    digest = await db_gateway.get_digest(callback_data.digest_id)
    
    text_digest = await td_manipulations(
        digest=digest,
        user_id=callback.from_user.id,
        show_category_keyboard=show_category_keyboard,
        language_code=language_code
        )

    buttons, objects_with_indexes = await get_buttons_and_objects(text_digest=text_digest)
    
    await callback.message.edit_text(
        text=callback.message.html_text,
        parse_mode='HTML',
        link_preview_options=callback.message.link_preview_options,
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons)
    )


@digest_router.callback_query(CategoryPaginationPrevious.filter())
async def render_digest_keyboard(
    callback: types.CallbackQuery,
    callback_data: CategoryPaginationPrevious,
    rabbit_service: RabbitService,
    kb_query_tool: KbQueryTool,
    bot: Bot,
):
    await kb_query_tool.change_kb_position(message_id=callback.message.message_id,
                                           direction='previous',
                                           category_pages=callback_data.category_pages)

    await callback.answer()
    await rabbit_service.change_digest_keyboard(
        user_id=callback.from_user.id,
        bot_id=bot.id,
        digest_id=callback_data.digest_id,
        offset=callback_data.new_offset,
        message_id=callback.message.message_id,
        with_subscribe_suggestions=callback_data.with_subscribe_suggestions,
    )


@digest_router.callback_query(DigestToVoice.filter())  # , Premium(PremiumLevel.GOLD, "Аудио-версия дайджеста"))
@flags.is_using_postgres
async def voice_answer(
    callback: types.CallbackQuery,
    callback_data: DigestToVoice,
    rabbit_service: RabbitService,
    db_gateway: DatabaseGatewayAsync,
    _session: AsyncSession,
    bot: Bot,
):

    opening_message = await callback.bot.send_message(
        callback.message.chat.id,
        _('wait_voice_generating'),
        disable_notification=True
    )
    await callback.answer()

    await rabbit_service.edit_digest_offset_command(
        user_id=callback.from_user.id,
        bot_id=bot.id,
        digest_id=callback_data.digest_id,
        offset=callback_data.new_offset,
        message_id=callback.message.message_id,
        category=callback_data.category,
        # voice_pressed=True,
        with_subscribe_suggestions=callback_data.with_subscribe_suggestions,
    )

    summaries_for_tts = (await TextDigest.prepare_summaries(
        digest_id=callback_data.digest_id,
        summaries=await db_gateway.get_summaries_by_digest_id(
            callback_data.digest_id,
            with_channels=True,
        ),
        user_id=callback.from_user.id,
        session=_session
    ))

    try:
        await asyncio.gather(
            *(
                SummaryTTSUploader.generate_and_upload_tts_for_summary(
                    summary.id,
                    summary.text,
                )
                for summary in summaries_for_tts if not summary.tts_generated
            )
        )

        await callback.bot.send_voice(
            callback.message.chat.id,
            voice=BufferedInputFile(
                await VoiceGluer.download_and_clue_voices(
                    (summary.id for summary in summaries_for_tts)  # NOQA
                ),
                filename="voice_answer"
            ),
            caption=_('your_voice_digest')
        )
    except Exception as error:  # NOQA
        if isinstance(error, TelegramBadRequest) and 'VOICE_MESSAGES_FORBIDDEN' in str(error):
            await callback.bot.send_message(callback.message.chat.id, text=_('voice_message_forbidden'), disable_notification=True)
        else:
            await callback.bot.send_message(callback.message.chat.id, text=_('voice_error'), disable_notification=True)
        raise
    finally:
        await opening_message.delete()


@digest_router.message(Command(commands=['digest']))
@digest_router.message(F.text == __('main_kb_instant_news'))
async def request_digest(message: types.Message, rabbit_service: RabbitService, bot: Bot):
    await rabbit_service.request_digest(
        user_id=message.from_user.id,
        bot_id=bot.id,
    )


@digest_router.callback_query(AdvertisementData.filter())
async def show_ad(
    callback: types.CallbackQuery,
    callback_data: AdvertisementData,
    rabbit_service: RabbitService,
    ads_service: AdsService,
    bot: Bot,
):
    current_ad = await ads_service.get_current_ad()
    if not current_ad:
        await callback.answer()
        if callback_data.new_offset != 0:
            await rabbit_service.edit_digest_offset_command(
                user_id=callback.from_user.id,
                bot_id=bot.id,
                digest_id=callback_data.digest_id,
                offset=callback_data.new_offset,
                message_id=callback.message.message_id,
                category=callback_data.category,
                with_subscribe_suggestions=callback_data.with_subscribe_suggestions,
            )
        else:
            row = list()
            row.append(types.InlineKeyboardButton(
                text=_('previous'),
                callback_data=DigestNavigationData(
                    digest_id=callback_data.digest_id,
                    new_offset=0,
                    category=0,
                    with_subscribe_suggestions=callback_data.with_subscribe_suggestions
                ).pack()
            ))
            try:
                await callback.message.edit_text(
                    'Отличная работа, всё прочитано!',
                    reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[row]),
                )
            except TelegramBadRequest as e:
                if 'message to edit not found' in str(e):
                    await callback.message.answer(
                        'Отличная работа, всё прочитано!',
                        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[row]),
                    )
                    return

                raise
        return

    min_timestamp = int(datetime.utcnow().timestamp()) + settings.ADS_PAGINATION_TIMEOUT_SECS
    row = list()
    row.append(types.InlineKeyboardButton(
        text=_('previous'),
        callback_data=DigestNavigationData(
            min_timestamp=min_timestamp,
            digest_id=callback_data.digest_id,
            new_offset=0,
            category=0,
            with_subscribe_suggestions=callback_data.with_subscribe_suggestions
        ).pack()
    ))
    if callback_data.new_offset != 0:
        row.append(types.InlineKeyboardButton(
            text=_('next'),
            callback_data=DigestNavigationData(
                min_timestamp=min_timestamp,
                digest_id=callback_data.digest_id,
                new_offset=callback_data.new_offset,
                category=0,
                with_subscribe_suggestions=callback_data.with_subscribe_suggestions
            ).pack()
        ))
    if current_ad.media:
        link_preview = LinkPreviewOptions(is_disabled=True)  # False, url=current_ad.media, show_above_text=True)
    else:
        link_preview = LinkPreviewOptions(is_disabled=True)
    try:
        await callback.message.edit_text(
            current_ad.text,
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[row]),
            link_preview_options=link_preview,
        )
    except TelegramBadRequest as e:
        if 'message to edit not found' in str(e):
            await callback.message.answer(
                current_ad.text,
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[row]),
                link_preview_options=link_preview,
            )
            return

        raise
