
import logging
from telegram import __version__ as TG_VER
try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]
if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )
from telegram import (
    KeyboardButton,
    KeyboardButtonPollType,
    Poll,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    PollAnswerHandler,
    PollHandler,
    filters,
    ConversationHandler
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Define conversation states
QUESTION, OPTIONS, CONFIRM = range(3)

async def handle_unexpected_state(update, context):
    await context.bot.send_message(chat_id=update.message.chat_id, text="An unexpected error occurred. Please start over.")
    return ConversationHandler.END

async def start(update, context):
    """Send a message when the command /start is issued."""
    await update.message.reply_text('Please select /poll to create a poll.')

async def poll(update, context):
    """Create a poll with user-specified question and options"""
    await update.message.reply_text("Please enter the question for your poll:")
    return QUESTION


async def receive_question(update, context):
    """Receive and store the user-specified question"""
    question = update.message.text
    context.user_data["question"] = question
    await update.message.reply_text("Please enter the first option for your poll:")
    return OPTIONS

async def receive_options(update, context):
    """Receive and store the user-specified options"""
    option = update.message.text
    if "options" not in context.user_data:
        context.user_data["options"] = []
    context.user_data["options"].append(option)
    reply_keyboard = [['Enter another option', 'No more options']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    await update.message.reply_text("Would you like to enter another option?", reply_markup=markup)
    return CONFIRM

async def confirm_options(update, context):
    """Confirm the user-specified options and create the poll"""
    response = update.message.text
    if response == 'Enter another option':
        await update.message.reply_text("Please enter another option:")
        return OPTIONS
    elif response == 'No more options':
        question = context.user_data["question"]
        options = context.user_data["options"]
        message = await context.bot.send_poll(update.message.chat_id, question, options,  is_anonymous=False,
        allows_multiple_answers=True,)
        payload = {
            message.poll.id: {
                "questions": question,
                "message_id": message.message_id,
                "chat_id": update.effective_chat.id,
                "answers": 0,
            }
        }
        context.bot_data.update(payload)
        await update.message.reply_text("Poll created!")
        context.user_data.clear()
        return ConversationHandler.END
async def receive_poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Summarize a users poll vote"""
    answer = update.poll_answer
    answered_poll = context.bot_data[answer.poll_id]
    try:
        questions = answered_poll["questions"]
    # this means this poll answer update is from an old poll, we can't do our answering then
    except KeyError:
        return
    selected_options = answer.option_ids
    answer_string = ""
    for question_id in selected_options:
        if question_id != selected_options[-1]:
            answer_string += questions[question_id] + " and "
        else:
            answer_string += questions[question_id]
   
    answered_poll["answers"] += 1
    # Close poll after three participants voted
   

async def cancel(update, context):
    """Cancel the poll creation process"""
    await update.message.reply_text("Poll creation process canceled.")
    return ConversationHandler.END

def main() -> None:
    """Run bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token("TOKEN").build()
    application.add_handler(CommandHandler("start", start))
    conversation_handler = ConversationHandler(
    entry_points=[CommandHandler("poll", poll)],
    states={
        QUESTION: [MessageHandler(filters.ALL, receive_question)],
        OPTIONS: [MessageHandler(filters.ALL, receive_options)],
        CONFIRM: [MessageHandler(filters.ALL, confirm_options)]
    },
    fallbacks=[CommandHandler('cancel', cancel),MessageHandler(filters.ALL, handle_unexpected_state)])
    application.add_handler(conversation_handler)
    application.add_handler(PollAnswerHandler(receive_poll_answer))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()
