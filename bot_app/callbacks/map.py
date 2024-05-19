from aiogram.filters.callback_data import CallbackData


class AdvertisementData(CallbackData, prefix='ads'):
    digest_id: int
    new_offset: int
    category: int
    with_subscribe_suggestions: bool


class DigestNavigationData(CallbackData, prefix='digest'):
    min_timestamp: int | None = None
    digest_id: int
    new_offset: int
    category: int
    with_subscribe_suggestions: bool


class DigestToVoice(CallbackData, prefix='digest_voice'):
    digest_id: int
    new_offset: int
    category: int
    voice_pressed: bool
    with_subscribe_suggestions: bool


class CategorylData(CallbackData, prefix='category'):
    digest_id: int
    new_offset: int
    category: int
    with_subscribe_suggestions: bool
    

class GetFullDigest(CallbackData, prefix='fulldigest'):
    digest_id: int
    with_subscribe_suggestions: bool
    

class CategoryPaginationNext(CallbackData, prefix='catnext'):
    digest_id: int
    new_offset: int
    category_pages: int
    with_subscribe_suggestions: bool
    
    
class CategoryPaginationPrevious(CallbackData, prefix='catprevious'):
    digest_id: int
    new_offset: int
    category_pages: int
    with_subscribe_suggestions: bool
    
    
class ShowCategories(CallbackData, prefix='show_categories'):
    digest_id: int
    new_offset: int
    show_categories_kb: bool
    with_subscribe_suggestions: bool


class DisLikeEvent(CallbackData, prefix='dislike_event'):
    pass


class LikeEvent(CallbackData, prefix='like_event'):
    pass


class MapCallback(CallbackData, prefix='map'):
    pass

class ExpandedSearchData(CallbackData, prefix='expanded_search'):
    summary_id: int
    
class ExpandedWebSearchData(CallbackData, prefix='expanded_web_search'):
    user_query_hash: int