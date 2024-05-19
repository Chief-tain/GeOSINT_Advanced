from aiogram import F, Router
from aiogram.filters.chat_member_updated import ChatMemberUpdatedFilter, MEMBER, KICKED
from aiogram.types import ChatMemberUpdated

from bot_app.application.user.service import UserService

block_router = Router()
block_router.my_chat_member.filter(F.chat.type == 'private')


@block_router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=KICKED))
async def user_blocked_bot(event: ChatMemberUpdated, user_service: UserService):
    await user_service.disable_user(event.from_user.id)


@block_router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=MEMBER))
async def user_unblocked_bot(event: ChatMemberUpdated, user_service: UserService):
    await user_service.enable_user(event.from_user.id)
