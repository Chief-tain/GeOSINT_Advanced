from aiogram import F, Router, types
from aiogram.utils.chat_action import ChatActionSender
from aiogram.utils.i18n import gettext as _
from aiogram.fsm.context import FSMContext

from bot_app.application.hasgtags import HashtagApp
from bot_app.application.hasgtags import HashtagsExtractorMini
from bot_app.application.hasgtags.lang_names import language_names
from bot_app.application import WebSearchChatGPTService
from bot_app.tg.filters.premium import Premium, PremiumLevel
from bot_app.tg.keyboards.web_search import expanded_web_search_kb
from bot_app.tg.states.web_search import WebSearch

from shared.telegram.callbacks.digest import ExpandedWebSearchData
from shared.settings import LOCAL_PROMT_STYLING

import logging

web_search_router = Router()
tag_extractor = HashtagsExtractorMini()


@web_search_router.message(
    F.text,
    ~F.via_bot,
    # Premium(PremiumLevel.GOLD, "Поиск с AI-ассистентом"),
    flags={
        "enable_sequential_request": True,
        "key_sequential_request": "web_search"
    }
)
async def web_search(
    message: types.Message,
    hashtag_app: HashtagApp,
    state: FSMContext
):
    MIN_LENGTH_QUERY: int = 15
    RELEVANT_RESPONCE_LEHGTH: int = 250
    EXPANDED_SEARCH_LIMIT: int = 10
    
    if len(message.text) <= MIN_LENGTH_QUERY:
        await message.answer(_('web_search_failed_short_query'))
        return True
    
    async with ChatActionSender.typing(bot=message.bot, chat_id=message.chat.id):
        openning_message = await message.answer(_('openning_message'))
        
        language, tag_list = tag_extractor.get_summary_hashtags(text=message.text)
        
        data, links, language = await hashtag_app.search_by_user_query(
            language=language,
            tag_list=tag_list
            )
        
        logging.info(f'data: {data}')
        logging.info(f'language: {language_names[language]}')
        logging.info(f'tag_list: {tag_list}')
        
        response = await WebSearchChatGPTService(
            openning_message,
            model='gpt-3.5-turbo-0125'
            )._process_chat_completions(message.text, promt_styling=LOCAL_PROMT_STYLING.format(user_query=message.text, news=data, language=language_names[language]))
        
        response = response.choices[0].message.content
        
        if len(response) > RELEVANT_RESPONCE_LEHGTH:
            response += f'\n\n Источники: {links}'
        
        await openning_message.delete()
        
        state_data: dict = await state.get_data()
        
        if 'expanded_search_queries' not in state_data:
            state_data['expanded_search_queries'] = {hash(message.text): message.text}
        else:
            if len(state_data['expanded_search_queries']) >= EXPANDED_SEARCH_LIMIT:
                first_key = next(iter(state_data['expanded_search_queries']))
                del state_data['expanded_search_queries'][first_key]
            state_data['expanded_search_queries'][hash(message.text)] = message.text
        await state.set_data(state_data)
        
        await message.answer(response, reply_markup=expanded_web_search_kb(user_query_hash=hash(message.text)))


@web_search_router.callback_query(ExpandedWebSearchData.filter())
async def expanded_web_search(
    callback: types.CallbackQuery,
    callback_data: ExpandedWebSearchData,
    state: FSMContext
): 
    await callback.message.edit_reply_markup()
    state_data: dict = await state.get_data()
    
    try:
        user_query_text = state_data['expanded_search_queries'][str(callback_data.user_query_hash)]
    except KeyError:
        await callback.message.answer(_('expanded_search_key_lost'))
    else:
        del state_data['expanded_search_queries'][str(callback_data.user_query_hash)]
        await state.set_data(state_data)
        
        async with ChatActionSender.typing(bot=callback.bot, chat_id=callback.message.chat.id):
            openning_message = await callback.message.answer(_('openning_message'))
            response = await WebSearchChatGPTService(openning_message).search(user_query_text)
            await openning_message.delete()
            await callback.message.answer(response)
    