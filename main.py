import io
import logging
import os

from dotenv import load_dotenv
from pydub import AudioSegment
from telegram import Update, ChatAction
from telegram.ext import Updater, CallbackContext, MessageHandler, Filters, CommandHandler

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

MAX_SMILES_DETECTED = os.getenv('MAX_SMILES_DETECTED', 60)


def start(update: Update, context: CallbackContext):
    update.message.reply_text("))0))")


def respond_join_audio(update: Update, context: CallbackContext):
    logger.info("Incoming message: '%s'", str(update.message.text))
    audios = [context.bot_data['audio_mapping'][c]
              for c in update.message.text
              if c in context.bot_data['audio_mapping'].keys()]
    if audios:
        if len(audios) > MAX_SMILES_DETECTED:
            update.message.reply_text(f"Too many smiles detected ({len(audios)}), "
                                      f"should not exceed {MAX_SMILES_DETECTED}")
            logger.warning(f"Too many smiles ({len(audios)})")
            return

        context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.RECORD_AUDIO)
        result_audio = sum(audios)
        audio_bytes = io.BytesIO()
        result_audio.export(audio_bytes, format='mp3')

        update.message.reply_audio(audio_bytes, title='))0)).mp3.mp3.mp3.mp3.mp3.mp3')
        logger.info("Sent %d seconds of audio memes", result_audio.duration_seconds)
    else:
        logger.info("No appropriate smiles detected")


def init_bot_data(bot_data: dict):
    # format: <smile1>,<smile2>:<audio_path1>;<smile3>:<audio_path2>...
    smile_to_audio_path = os.getenv('SMILE_TO_AUDIO_PATH', None)

    if smile_to_audio_path is None:
        bot_data['audio_mapping'] = {}
    else:
        bad_pairs = [pair for pair in smile_to_audio_path.split(';') if ':' not in pair]
        if bad_pairs:
            raise ValueError("Bad pairs, format: <smile1>,<smile2>:<audio_path1>;<smile3>:<audio_path2>...", bad_pairs)

        bot_data['audio_mapping'] = {}
        pairs = [pair.split(':') for pair in smile_to_audio_path.split(';') if pair]
        for smiles, audio_path in pairs:
            audio = AudioSegment.from_file(audio_path)

            splitted_smiles = [smile for smile in smiles.split(',') if smile]
            for smile in splitted_smiles:
                if smile in bot_data['audio_mapping'].keys():
                    raise ValueError('Repeated smile', smile)

                bot_data['audio_mapping'][smile] = audio
        logger.debug("Appropriate smiles: %s", bot_data['audio_mapping'].keys())


def main() -> None:
    updater = Updater(os.getenv('TOKEN'))
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(MessageHandler(Filters.text, respond_join_audio))

    init_bot_data(dispatcher.bot_data)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
