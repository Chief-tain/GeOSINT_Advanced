from typing import Any, Dict, Union
from enum import IntEnum
from aiogram.filters import BaseFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import TelegramObject, CallbackQuery, Message
from aiogram.utils.i18n import gettext as _


class PremiumLevel(IntEnum):
    FREE = -1
    SILVER = 0
    GOLD = 100


class Premium(BaseFilter):
    def __init__(self, premium_level: int | PremiumLevel = PremiumLevel.FREE, feature_name: str | None = None):
        self.premium_level = premium_level
        self.feature_name = feature_name
        super().__init__()

    async def __call__(
        self,
        event: TelegramObject,
        *,
        state: FSMContext,
        **kwargs: Any
    ) -> Union[bool, Dict[str, Any]]:
        data = await state.get_data()
        user_premium_level = data.get('premium')
        if user_premium_level is None:
            user_premium_level = PremiumLevel.FREE
        if user_premium_level < self.premium_level:
            if self.premium_level == 0:
                level_name = 'Silver'
            elif self.premium_level == 100:
                level_name = 'Gold'
            else:
                level_name = '<LEVEL NAME>'
            if self.feature_name:
                text = _('named_feature_blocked {feature_name} {required_level_name}')
                feature_name = _(self.feature_name)
                text = text.format(feature_name=feature_name, required_level_name=level_name)
            else:
                text = _('unnamed_feature_blocked {required_level_name}')
                text = text.format(required_level_name=level_name)
            if isinstance(event, CallbackQuery):
                await event.message.answer(text)
                await event.answer()
            elif isinstance(event, Message):
                await event.answer(text)
            return False
        return True
