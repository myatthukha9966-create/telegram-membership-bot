from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from datetime import datetime, timedelta, timezone
import json
import os


BOT_TOKEN = "8061971526:AAHQRDL3mYJPyouAzdNvWYA2mP9ZD1H5afU"
ADMIN_ID = 8598152114
CHANNEL_ID = -1004395282788

MYANMAR_TZ = timezone(timedelta(hours=6, minutes=30))
MEMBERSHIP_FILE = "memberships.json"


# =========================
# PAYMENT TEXT
# =========================

PAYMENT_TEXT = (
    "Payment Methods\n\n"
    "KPay - +959892919730\n"
    "Myat Thu Kha\n\n"
    "Wave Pay - +959660979163\n"
    "Zaw Moe Oo\n\n"
    'Note မှာ "ငွေပေးချေခြင်း" ဆိုတာပဲရေးပေးပါ'
)


# =========================
# MEMBERSHIP SAVE / LOAD
# =========================

def load_memberships():
    if not os.path.exists(MEMBERSHIP_FILE):
        return {}

    try:
        with open(MEMBERSHIP_FILE, "r", encoding="utf-8") as file:
            return json.load(file)

    except Exception as error:
        print(f"❌ Could not load memberships: {error}")
        return {}


def save_memberships(memberships):
    try:
        with open(MEMBERSHIP_FILE, "w", encoding="utf-8") as file:
            json.dump(
                memberships,
                file,
                ensure_ascii=False,
                indent=4
            )

    except Exception as error:
        print(f"❌ Could not save memberships: {error}")


# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [
            InlineKeyboardButton(
                "1 Month Membership",
                callback_data="one_month"
            )
        ]
    ]

    await update.message.reply_text(
        "👋 မင်္ဂလာပါ!\n\n"
        "Membership ဝင်ရောက်ရန်\n"
        "အောက်က Button ကိုနှိပ်ပါ 👇",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================
# PLAN SELECTED
# =========================

async def plan_selected(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query
    await query.answer()

    keyboard = [
        [
            InlineKeyboardButton(
                "✨ Payment ပြီးပါပြီ ✨",
                callback_data="payment_done"
            )
        ]
    ]

    await query.edit_message_text(
        "1 Month Membership\n\n"
        "စေတနာကြေးသာကောက်ခံတာမို့ "
        "ကိုယ်အဆင်ပြေသလောက် ထည့်ပေးလို့ရပါတယ်\n\n"
        f"{PAYMENT_TEXT}\n\n"
        "✨ Payment ပြီးလျှင် အောက်က Button ကိုနှိပ်ပါ ✨",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================
# PAYMENT DONE
# =========================

async def payment_done(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query
    await query.answer()

    waiting_users = context.application.bot_data.setdefault(
        "waiting_for_screenshot",
        set()
    )

    waiting_users.add(query.from_user.id)

    await query.edit_message_text(
        "📸 Payment Screenshot လေးကို "
        "ဒီနေရာမှာ ပေးပို့ပေးပါနော်။\n\n"
        "ငွေလွှဲဝင်ရောက်မှုကို စစ်ဆေးပြီး "
        "အတည်ပြုပေးပါမယ်။"
    )


# =========================
# RECEIVE SCREENSHOT
# =========================

async def receive_screenshot(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    print("📸 PHOTO RECEIVED!")

    waiting_users = context.application.bot_data.setdefault(
        "waiting_for_screenshot",
        set()
    )

    user = update.effective_user

    if user.id not in waiting_users:
        print(
            f"❌ User {user.id} is not waiting for screenshot"
        )
        return

    print(
        f"✅ User {user.id} is waiting for screenshot"
    )

    caption = (
        "💳 New Payment Submission\n\n"
        f"👤 Name: {user.full_name}\n"
        f"🆔 User ID: {user.id}\n"
        f"🔗 Username: @{user.username if user.username else 'None'}\n\n"
        "Payment ကို စစ်ဆေးပေးပါ။"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "✅ CONFIRM",
                callback_data=f"confirm_{user.id}"
            ),
            InlineKeyboardButton(
                "❌ REJECT",
                callback_data=f"reject_{user.id}"
            ),
        ],
        [
            InlineKeyboardButton(
                "🔄 TRY AGAIN",
                callback_data=f"tryagain_{user.id}"
            ),
        ],
    ]

    try:

        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=update.message.photo[-1].file_id,
            caption=caption,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        print(
            f"✅ Screenshot sent to admin: {user.id}"
        )

        waiting_users.discard(user.id)

        await update.message.reply_text(
            "✅ Screenshot လက်ခံရရှိပါပြီ။\n\n"
            "Payment ကို စစ်ဆေးနေပါတယ်။\n"
            "အတည်ပြုပြီးတာနဲ့ "
            "Membership access ပေးပါမယ်။"
        )

    except Exception as error:

        print(
            f"❌ Could not send screenshot to admin: {error}"
        )

        await update.message.reply_text(
            "❌ Screenshot ပို့ရာမှာ ပြဿနာဖြစ်သွားပါတယ်။\n\n"
            "ခဏနေပြီး Screenshot ကို ပြန်ပို့ပေးပါနော်။"
        )


# =========================
# EXPIRY WARNING
# =========================

async def send_expiry_warning(
    context: ContextTypes.DEFAULT_TYPE
):

    job = context.job

    if not job or not job.data:
        return

    user_id = job.data["user_id"]

    memberships = load_memberships()

    membership = memberships.get(
        str(user_id)
    )

    if not membership:
        return

    if membership.get("status") != "active":
        return

    try:

        expiry_time = datetime.fromisoformat(
            membership["expiry_time"]
        )

    except Exception as error:

        print(
            f"❌ Invalid expiry time for {user_id}: {error}"
        )

        return

    now = datetime.now(
        MYANMAR_TZ
    )

    if now >= expiry_time:
        return

    keyboard = [
        [
            InlineKeyboardButton(
                "🔄 Renew Membership",
                callback_data="one_month"
            )
        ]
    ]

    try:

        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "⚠️ Membership သတိပေးချက်\n\n"
                "သင့် Membership သက်တမ်းကုန်ဆုံးရန် "
                "၁ မိနစ်သာ ကျန်ရှိပါတော့တယ်။\n\n"
                f"⏰ Expiry:\n"
                f"{expiry_time.strftime('%d %B %Y, %I:%M:%S %p')}\n\n"
                "ဆက်လက်အသုံးပြုလိုပါက "
                "အောက်က button ကိုနှိပ်ပြီး "
                "Membership အသစ်ပြန်လည်ဝင်ရောက်နိုင်ပါတယ်။"
            ),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        print(
            f"🔔 Warning sent to user: {user_id}"
        )

    except Exception as error:

        print(
            f"❌ Could not send warning to {user_id}: {error}"
        )


# =========================
# EXPIRE MEMBERSHIP
# =========================

async def expire_membership(
    context: ContextTypes.DEFAULT_TYPE
):

    job = context.job

    if not job or not job.data:
        return

    user_id = job.data["user_id"]

    memberships = load_memberships()

    membership = memberships.get(
        str(user_id)
    )

    if not membership:
        return

    if membership.get("status") != "active":
        return

    try:

        await context.bot.ban_chat_member(
            chat_id=CHANNEL_ID,
            user_id=user_id
        )

        await context.bot.unban_chat_member(
            chat_id=CHANNEL_ID,
            user_id=user_id,
            only_if_banned=True
        )

        print(
            f"✅ User removed from channel: {user_id}"
        )

    except Exception as error:

        print(
            f"❌ Could not remove user {user_id}: {error}"
        )

    membership["status"] = "expired"

    membership["expired_at"] = datetime.now(
        MYANMAR_TZ
    ).isoformat()

    save_memberships(
        memberships
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "🔄 Renew Membership",
                callback_data="one_month"
            )
        ]
    ]

    try:

        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "⏰ Membership Expired\n\n"
                "သင့် Membership သက်တမ်း "
                "ကုန်ဆုံးသွားပါပြီ။\n\n"
                "ဆက်လက်အသုံးပြုလိုပါက "
                "အောက်က button ကိုနှိပ်ပြီး "
                "Membership အသစ်ပြန်လည်ဝင်ရောက်နိုင်ပါတယ်။"
                "ကျေးဇူးတင်ပါတယ်❤️"
            ),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    except Exception as error:

        print(
            f"❌ Could not message user {user_id}: {error}"
        )

    print(
        f"⏰ Membership expired: {user_id}"
    )


# =========================
# SCHEDULE MEMBERSHIP JOBS
# =========================

def schedule_membership_jobs(
    application,
    user_id,
    expiry_time
):

    if application.job_queue is None:

        print(
            "❌ JobQueue is not available.\n"
            'Run: pip install "python-telegram-bot[job-queue]"'
        )

        return

    now = datetime.now(
        MYANMAR_TZ
    )

    warning_time = (
        expiry_time -
        timedelta(minutes=1)
    )

    if warning_time > now:

        application.job_queue.run_once(
            send_expiry_warning,
            when=warning_time,
            data={
                "user_id": user_id
            },
            name=f"warning_{user_id}"
        )

        print(
            f"🔔 Warning scheduled for "
            f"{user_id}: {warning_time}"
        )

    if expiry_time > now:

        application.job_queue.run_once(
            expire_membership,
            when=expiry_time,
            data={
                "user_id": user_id
            },
            name=f"expiry_{user_id}"
        )

        print(
            f"⏰ Expiry scheduled for "
            f"{user_id}: {expiry_time}"
        )


# =========================
# RESTORE JOBS AFTER RESTART
# =========================

async def post_init(
    application
):

    print(
        "🔄 Checking saved memberships..."
    )

    memberships = load_memberships()

    now = datetime.now(
        MYANMAR_TZ
    )

    for user_id, membership in memberships.items():

        if membership.get("status") != "active":
            continue

        try:

            expiry_time = datetime.fromisoformat(
                membership["expiry_time"]
            )

            user_id_int = int(
                user_id
            )

            if expiry_time <= now:

                try:

                    await application.bot.ban_chat_member(
                        chat_id=CHANNEL_ID,
                        user_id=user_id_int
                    )

                    await application.bot.unban_chat_member(
                        chat_id=CHANNEL_ID,
                        user_id=user_id_int,
                        only_if_banned=True
                    )

                    print(
                        f"✅ Removed expired user: {user_id}"
                    )

                except Exception as error:

                    print(
                        f"❌ Could not remove expired user "
                        f"{user_id}: {error}"
                    )

                membership["status"] = "expired"

                membership["expired_at"] = (
                    now.isoformat()
                )

                continue

            schedule_membership_jobs(
                application,
                user_id_int,
                expiry_time
            )

            print(
                f"♻️ Restored membership: {user_id}"
            )

        except Exception as error:

            print(
                f"❌ Could not restore membership "
                f"{user_id}: {error}"
            )

    save_memberships(
        memberships
    )

    print(
        "✅ Membership jobs restored."
    )


# =========================
# ADMIN ACTION
# =========================

async def admin_action(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if query.from_user.id != ADMIN_ID:

        await query.answer(
            "ဒီလုပ်ဆောင်ချက်ကို Admin ပဲအသုံးပြုနိုင်ပါတယ်။",
            show_alert=True
        )

        return

    await query.answer()

    data = query.data


    # =========================
    # CONFIRM
    # =========================

    if data.startswith("confirm_"):

        user_id = int(
            data.split("_")[1]
        )

        start_time = datetime.now(
            MYANMAR_TZ
        )

        expiry_time = (
            start_time +
            timedelta(minutes=2)
        )

        start_text = start_time.strftime(
            "%d %B %Y, %I:%M:%S %p"
        )

        expiry_text = expiry_time.strftime(
            "%d %B %Y, %I:%M:%S %p"
        )

        invite_link = (
            await context.bot.create_chat_invite_link(
                chat_id=CHANNEL_ID,
                member_limit=1
            )
        )

        memberships = load_memberships()

        memberships[str(user_id)] = {
            "user_id": user_id,
            "start_time": start_time.isoformat(),
            "expiry_time": expiry_time.isoformat(),
            "status": "active",
            "invite_link": invite_link.invite_link
        }

        save_memberships(
            memberships
        )

        schedule_membership_jobs(
            context.application,
            user_id,
            expiry_time
        )

        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "🎉 Payment Confirmed!\n\n"
                "Membership ကို "
                "အတည်ပြုပေးလိုက်ပါပြီ။\n\n"
                f"📅 Membership စတင်ချိန်\n"
                f"{start_text}\n\n"
                f"⏰ Membership သက်တမ်းကုန်ချိန်\n"
                f"{expiry_text}\n\n"
                "🔗 Channel Join Link:\n"
                f"{invite_link.invite_link}\n\n"
                "⚠️ ဒီ link ကို "
                "တစ်ယောက်သာ အသုံးပြုနိုင်ပါတယ်။"
            )
        )

        await query.edit_message_caption(
            caption=(
                query.message.caption +
                "\n\n✅ CONFIRMED"
            )
        )

        print(
            f"✅ TEST Membership created: "
            f"{user_id} | "
            f"Start: {start_text} | "
            f"Expires: {expiry_text}"
        )


    # =========================
    # REJECT
    # =========================

    elif data.startswith("reject_"):

        user_id = int(
            data.split("_")[1]
        )

        waiting_users = (
            context.application.bot_data.setdefault(
                "waiting_for_screenshot",
                set()
            )
        )

        # IMPORTANT:
        # After REJECT, user is allowed
        # to send a new screenshot.

        waiting_users.add(
            user_id
        )

        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "❌ Payment ကို "
                "အတည်မပြုနိုင်သေးပါဘူး။\n\n"
                "Payment information မှာ "
                "ပြဿနာရှိနေပါတယ်။\n\n"
                "ကျေးဇူးပြုပြီး Payment ကို "
                "ပြန်လည်စစ်ဆေးပြီး "
                "လိုအပ်ပါက Screenshot အသစ် "
                "ပြန်ပို့ပေးပါနော်။\n\n"
                f"{PAYMENT_TEXT}\n\n"
                "ငွေလွှဲပြီးပါက Screenshot အသစ်ကို "
                "ဒီ chat ထဲမှာ ပြန်ပို့ပေးပါနော်။"
            )
        )

        await query.edit_message_caption(
            caption=(
                query.message.caption +
                "\n\n❌ REJECTED"
            )
        )

        print(
            f"❌ Payment rejected. "
            f"Waiting for new screenshot: {user_id}"
        )


    # =========================
    # TRY AGAIN
    # =========================

    elif data.startswith("tryagain_"):

        user_id = int(
            data.split("_")[1]
        )

        waiting_users = (
            context.application.bot_data.setdefault(
                "waiting_for_screenshot",
                set()
            )
        )

        # IMPORTANT:
        # After TRY AGAIN, user is allowed
        # to send a new screenshot.

        waiting_users.add(
            user_id
        )

        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "⚠️ Payment ပမာဏ "
                "မလုံလောက်သေးပါဘူး။\n\n"
                "Membership access ရရှိရန် "
                "အနည်းဆုံး 100 ကျပ် "
                "ပေးချေရပါမယ်။\n\n"
                f"{PAYMENT_TEXT}\n\n"
                "ငွေလွှဲပြီးပါက Screenshot အသစ်ကို "
                "ဒီ chat ထဲမှာ ပြန်လည်ပေးပို့ပေးပါနော်။"
            )
        )

        await query.edit_message_caption(
            caption=(
                query.message.caption +
                "\n\n🔄 TRY AGAIN"
            )
        )

        print(
            f"🔄 Try again requested. "
            f"Waiting for new screenshot: {user_id}"
        )


# =========================
# ERROR HANDLER
# =========================

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE
):

    print(
        f"❌ BOT ERROR: {context.error}"
    )


# =========================
# APP
# =========================

app = (
    Application.builder()
    .token(BOT_TOKEN)
    .post_init(post_init)
    .build()
)


# =========================
# HANDLERS
# =========================

app.add_handler(
    CommandHandler(
        "start",
        start
    )
)

app.add_handler(
    CallbackQueryHandler(
        plan_selected,
        pattern="^one_month$"
    )
)

app.add_handler(
    CallbackQueryHandler(
        payment_done,
        pattern="^payment_done$"
    )
)

app.add_handler(
    MessageHandler(
        filters.PHOTO,
        receive_screenshot
    )
)

app.add_handler(
    CallbackQueryHandler(
        admin_action,
        pattern="^(confirm|reject|tryagain)_"
    )
)

app.add_error_handler(
    error_handler
)


# =========================
# RUN BOT
# =========================

print(
    "🤖 Bot is starting..."
)

print(
    "🇲🇲 Myanmar Time: UTC+6:30"
)

print(
    "💳 Payment system: READY"
)

print(
    "🔗 One-time invite link: READY"
)

print(
    "📅 TEST Membership: 2 MINUTES"
)

print(
    "🔔 TEST Expiry warning: "
    "1 MINUTE BEFORE EXPIRY"
)

print(
    "⏰ Auto expiry/kick: READY"
)

print(
    "💾 Membership database: READY"
)

print(
    "♻️ Restart recovery: READY"
)

print("")

app.run_polling()