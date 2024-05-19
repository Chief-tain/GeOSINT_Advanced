from aiogram import F, Router, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, WebAppInfo
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _, lazy_gettext as __

from bot_app.application import UserService
from shared.models import PaidSubscriptionType
from shared.telegram.callbacks.paid_subscriptions import ShowPlan, RealizeCreatedPayment, SetNextSubscription
from shared.yookassa import yookassa_helper


premium_router = Router()


def get_text_by_subscription_type(subscription_type: PaidSubscriptionType | None) -> str:
    subscription_type_name = get_subscription_name_by_type(subscription_type)
    text = _('premium_description_' + subscription_type_name + ' {price}')
    if subscription_type:
        text = text.format(price=subscription_type.price_monthly_rub)
    return text


def get_subscription_priority_by_type(subscription_type: PaidSubscriptionType | None) -> int:
    return subscription_type.priority if subscription_type else -1


def get_subscription_name_by_type(subscription_type: PaidSubscriptionType | None) -> str:
    return subscription_type.name if subscription_type else 'free'


@premium_router.message(F.text == __('premium_button'))
async def show_subscription_plans(
    message: types.Message,
    state: FSMContext,
    user_service: UserService,
):
    premium_level = (await state.get_data()).get('premium')

    current_paid_subscription = \
        await user_service.get_current_paid_subscription(telegram_id=message.from_user.id)
    longest_paid_subscription = \
        await user_service.get_longest_paid_subscription_of_user(telegram_id=message.from_user.id)

    if premium_level < 0 or not all((current_paid_subscription, longest_paid_subscription)):
        await state.update_data({'premium': -1})
        text = _('premium_description_free {price}')
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text='Free', callback_data='premium:free'),
                InlineKeyboardButton(text='Silver', callback_data='premium:silver'),
                InlineKeyboardButton(text='Gold', callback_data='premium:gold'),
            ],
            [
                InlineKeyboardButton(
                    text=_('keep_free_plan'),
                    callback_data='null'
                )
            ]
        ])
        await message.answer(text=text, reply_markup=markup)
        return

    user_info = await user_service.get_user(user_id=message.from_user.id)
    text = _('current_plan {plan}')
    text = text.format(plan=current_paid_subscription.type.name.capitalize())
    if user_info.payment_method_id:
        text += _('next_debit {date} {plan}').format(
            date=longest_paid_subscription.end_dt.strftime("%d-%m-%Y"),
            plan=longest_paid_subscription.next_type.name.capitalize()
        )
        btn_text = _('link_another_card')
    else:
        text += _('paid_till {date}').format(date=longest_paid_subscription.end_dt.strftime("%d-%m-%Y"))
        btn_text = _('link_card')
    markup = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text=btn_text,
            web_app=WebAppInfo(url=await yookassa_helper.link_new_bank_card(user_id=message.from_user.id))
        ),
        InlineKeyboardButton(
            text=_('choose_another_plan'),
            callback_data=f'premium:{current_paid_subscription.type.name}'
        ),
    ]])
    await message.answer(text=text, reply_markup=markup)


@premium_router.callback_query(ShowPlan.filter())
async def show_plan(c: CallbackQuery, callback_data: ShowPlan, state: FSMContext, user_service: UserService):
    payment_method_id = (await user_service.get_user(c.from_user.id)).payment_method_id

    current_subscription = await user_service.get_current_paid_subscription(c.from_user.id)
    current_subscription_type = current_subscription.type if current_subscription else None
    chosen_subscription_type = await user_service.get_subscription_type_by_name(callback_data.plan_name)

    if current_subscription_type is None and chosen_subscription_type is None:
        # keep free subscription
        btn_text = _('keep_plan {plan}').format(plan=get_subscription_name_by_type(current_subscription_type).capitalize())
        btn = InlineKeyboardButton(
            text=btn_text,
            callback_data='null'
        )
    elif chosen_subscription_type is None:
        # subscription cancel
        btn_text = _('cancel_plan')
        btn = InlineKeyboardButton(
            text=btn_text,
            callback_data='premium_cancel'
        )
    elif current_subscription_type is None:
        # transition from free to some subscription
        if payment_method_id:
            created_payment_id = await yookassa_helper.buy_subscription_auto(
                c.from_user.id,
                payment_method_id,
                chosen_subscription_type,
                only_create=True,
            )

            btn_text = _('change_plan {plan}').format(
                plan=get_subscription_name_by_type(chosen_subscription_type).capitalize()
            )
            btn = InlineKeyboardButton(
                text=btn_text,
                callback_data=RealizeCreatedPayment(
                    payment_id=created_payment_id,
                    current_subscription_priority=get_subscription_priority_by_type(current_subscription_type),
                ).pack()
            )
        else:
            btn_text = _('change_plan {plan}').format(
                plan=get_subscription_name_by_type(chosen_subscription_type).capitalize()
            )
            btn = InlineKeyboardButton(
                text=btn_text,
                web_app=WebAppInfo(
                    url=await yookassa_helper.link_bank_card_and_buy_subscription(
                        user_id=c.from_user.id,
                        subscription_type_id_to_buy_on_success=chosen_subscription_type.id,
                    )
                )
            )
    elif current_subscription_type.id == chosen_subscription_type.id:
        # keep some paid subscription
        btn_text = _('keep_plan {plan}').format(
            plan=get_subscription_name_by_type(current_subscription_type).capitalize()
        )
        btn = InlineKeyboardButton(
            text=btn_text,
            callback_data=SetNextSubscription(
                current_subscription_priority=get_subscription_priority_by_type(current_subscription_type),
                next_subscription_type_priority=get_subscription_priority_by_type(chosen_subscription_type),
            ).pack()
        )
    elif current_subscription_type.price_monthly_rub < chosen_subscription_type.price_monthly_rub:
        # transition from cheaper subscription to more expensive
        surcharge, split_dt = yookassa_helper.calculate_surcharge_for_subscription_replace(
                current_subscription,
                chosen_subscription_type,
            )

        if payment_method_id:
            created_payment_id = await yookassa_helper.buy_subscription_auto(
                c.from_user.id,
                payment_method_id,
                chosen_subscription_type,
                current_subscription.id,
                split_dt,
                surcharge,
                f'Переход {get_subscription_name_by_type(current_subscription_type).capitalize()} ->'
                f'{get_subscription_name_by_type(chosen_subscription_type).capitalize()}',
                only_create=True,
            )

            btn_text = _('change_plan {plan}').format(
                plan=get_subscription_name_by_type(chosen_subscription_type).capitalize()
            )
            btn = InlineKeyboardButton(
                text=btn_text,
                callback_data=RealizeCreatedPayment(
                    payment_id=created_payment_id,
                    current_subscription_priority=get_subscription_priority_by_type(current_subscription_type),
                ).pack()
            )
        else:
            btn_text = _('change_plan {plan}').format(
                plan=get_subscription_name_by_type(chosen_subscription_type).capitalize()
            )
            btn = InlineKeyboardButton(
                text=btn_text,
                web_app=WebAppInfo(
                    url=await yookassa_helper.link_bank_card_and_buy_subscription(
                        c.from_user.id,
                        chosen_subscription_type.id,
                        surcharge,
                        f'Переход {get_subscription_name_by_type(current_subscription_type).capitalize()} ->'
                        f'{get_subscription_name_by_type(chosen_subscription_type).capitalize()}',
                        current_subscription.id,
                        split_dt,
                    )
                )
            )
    else:
        # transition from cheaper subscription to more expensive
        btn_text = _('change_plan {plan}').format(
            plan=get_subscription_name_by_type(chosen_subscription_type).capitalize()
        )
        btn = InlineKeyboardButton(
            text=btn_text,
            callback_data=SetNextSubscription(
                current_subscription_priority=get_subscription_priority_by_type(current_subscription_type),
                next_subscription_type_priority=get_subscription_priority_by_type(chosen_subscription_type),
            ).pack()
        )

    context_data = await state.get_data()
    context_data.pop('premium', None)
    await state.set_data(context_data)

    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='Free', callback_data='premium:free'),
                InlineKeyboardButton(text='Silver', callback_data='premium:silver'),
                InlineKeyboardButton(text='Gold', callback_data='premium:gold'),
            ],
            [
                btn
            ]
        ]
    )

    await c.message.edit_text(text=get_text_by_subscription_type(chosen_subscription_type), reply_markup=markup)


@premium_router.callback_query(F.data == 'premium_cancel')
async def cancel_subscription(c: CallbackQuery, user_service: UserService):
    await c.answer()
    await user_service.remove_payment_method(c.from_user.id)
    subscription_info = await user_service.get_current_paid_subscription(telegram_id=c.from_user.id)
    text = _('current_plan {plan}').format(plan=subscription_info.type.name.capitalize())
    text += _('paid_till {date}').format(date=subscription_info.end_dt.strftime("%d-%m-%Y"))
    btn_text = _('link_card')
    markup = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(
                text=btn_text,
                web_app=WebAppInfo(url=await yookassa_helper.link_new_bank_card(user_id=c.from_user.id))
                ),
            InlineKeyboardButton(
                text=_('choose_another_plan'),
                callback_data=f'premium:{subscription_info.type.name}'
            ),
        ]]
    )
    await c.message.edit_text(text=text, reply_markup=markup)


@premium_router.callback_query(RealizeCreatedPayment.filter())
async def realize_created_payment(
        c: CallbackQuery,
        user_service: UserService,
        callback_data: RealizeCreatedPayment,
        state: FSMContext
):
    await c.answer()

    current_subscription = await user_service.get_current_paid_subscription(c.from_user.id)
    current_subscription_type = current_subscription.type if current_subscription else None

    payment_method_id = await user_service.get_user(c.from_user.id)

    if not payment_method_id:
        return await c.message.answer(
            _('retry_autopay_turned_off')
        )

    if get_subscription_priority_by_type(current_subscription_type) != callback_data.current_subscription_priority:
        return await c.message.answer(
            _('retry_plan_changed')
        )

    try:
        await yookassa_helper.realize_created_auto_payment(callback_data.payment_id)
    except yookassa_helper.IncorrectPaymentStatus:
        await c.message.answer(_('wait_payment_ok'))
    else:
        await c.message.answer(_('wait_payment'))

    context_data = await state.get_data()
    context_data.pop('premium', None)
    await state.set_data(context_data)


@premium_router.callback_query(SetNextSubscription.filter())
async def realize_created_payment(
        c: CallbackQuery,
        user_service: UserService,
        callback_data: SetNextSubscription,
        state: FSMContext
):
    await c.answer()

    current_subscription = await user_service.get_current_paid_subscription(c.from_user.id)
    current_subscription_type = current_subscription.type if current_subscription else None

    payment_method_id = (await user_service.get_user(c.from_user.id)).payment_method_id

    if not payment_method_id:
        await c.message.answer(
            _('no_card_provided')
        )

    if get_subscription_priority_by_type(current_subscription_type) != callback_data.current_subscription_priority:
        return await c.message.answer(
            _('retry_plan_changed')
        )

    next_subscription_type = (
        next_subscription_type
        if (next_subscription_type := await user_service.get_subscription_type_by_priority(
            callback_data.next_subscription_type_priority
        )) else None
    )

    await user_service.change_next_type_id_by_subscription_id(current_subscription.id, next_subscription_type.id)

    await c.message.answer(
        _('next_plan {plan}').format(plan=get_subscription_name_by_type(next_subscription_type).capitalize())
    )

    context_data = await state.get_data()
    context_data.pop('premium', None)
    await state.set_data(context_data)
