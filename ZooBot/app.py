import telebot
from telebot import types
import time
from decouple import config

from quiz import Quiz

from service import send_email, greetings_generator1, greetings_generator2, start_generator, \
    get_totem_animal_data

from textinfo import default_response_text, help_text, \
    logo_photo, info_text, info_guardian_url, \
    guardian_text, send_message_text, contacts_text, share_result_text, serious_text


class LogoFileNotFoundException(Exception):
    pass


class BotManager:
    def __init__(self, token):
        """
        Initializes the BotManager with the provided Telegram API token.
        Sets up the bot instance and quiz object, and configures message and callback handlers.
        """
        self.bot = telebot.TeleBot(token)
        self.quiz = Quiz(self.bot)
        self.setup_handlers()
        self.totem_animal_data = None
        self.result_animal = None

    def start_bot(self):
        """
        Starts the bot's polling loop to continuously listen for new messages.
        """
        self.bot.polling(none_stop=True)

    def setup_handlers(self):
        """
        Sets up both message and callback handlers for the bot.
        """
        self.setup_message_handler()
        self.setup_callback_handler()

    def setup_message_handler(self):
        """
        Configures how the bot responds to different types of messages.
        Handles feedback messages and general commands like '/start', '/help', etc.
        """
        @self.bot.message_handler(func=lambda message: message.text.startswith('Feedback'))
        def handle_feedback_message(message):
            """
            Processes feedback messages from users, formats them into emails, and sends them.
            """
            try:
                if self.totem_animal_data is not None:
                    user_id = str(message.from_user.id)
                    full_name = f"{message.from_user.first_name} {message.from_user.last_name}"
                    subject = f'Feedback from User: {full_name}, ID: {user_id}'
                    results = message.text
                    print(results)
                    if send_email(results, subject):
                        send_message = 'Thank you for your feedback! It has been received and processed.'
                        self.bot.reply_to(message, send_message)
                    else:
                        send_message = 'Failed to process your request, please try again later.'
                        self.bot.reply_to(message, send_message)
            except TypeError:
                send_message = 'Quiz not completed yet, maybe you haven\'t formed an opinion yet.'
                answer = self.bot.send_message(message.chat.id, send_message)
                time.sleep(2)
                self.bot.delete_message(message.chat.id, message.message_id)
                time.sleep(4)
                self.bot.delete_message(message.chat.id, answer.message_id)

        @self.bot.message_handler(func=lambda message: True)
        def handle_messages(message):
            """
            General message handler that dispatches messages to appropriate handlers based on the command.
            """
            command_handlers = {
                'hello': self.send_greeting_with_buttons,
                '/start': self.send_start_menu_keyboard,
                '/help': self.send_help_message,
                '/info': self.send_info_message,
                '/contacts': self.send_contacts,
                'confirm': self.agreement
            }
            command = message.text.lower()
            handler = command_handlers.get(command, self.send_default_response)
            handler(message)

    def setup_callback_handler(self):
        """
        Configures how the bot responds to inline button presses (callback queries).
        """
        @self.bot.callback_query_handler(func=lambda call: True)
        def callback_handler(call):
            """
            Handles various inline button actions such as starting a quiz, showing results, etc.
            """
            command_handlers = {
                'learn_more': self.send_info_message,
                'become_guardian?': self.send_become_guardian_info,
                'start_quiz': self.send_start_quiz_message,
                'start': self.send_start_menu_keyboard,
                'help': self.send_help_message,
                'info': self.send_info_message,
                'contacts': self.send_contacts,
                'continue': self.processing_of_results,
                'restart_quiz': self.send_start_quiz_message,
                'show_result': self.show_totem_animal_info,
                'get_res': self.load_result_list,
                'become_a_guardian': self.become_a_guardian,
                'some_serious': self.some_serious,

            }
            for i in range(1, 5):
                command_handlers[f'answer_{i}'] = lambda message, idx=i: self.quiz.process_answer(message.chat.id, idx)
            command = call.data
            handler = command_handlers.get(command)
            if handler:
                handler(call.message)

    def send_greeting_with_buttons(self, message):
        """
        Sends a greeting message along with interactive buttons for further navigation.
        """
        markup = types.InlineKeyboardMarkup(row_width=2)
        button_start = types.InlineKeyboardButton("START", callback_data='start')
        button_help = types.InlineKeyboardButton("Help", callback_data='help')
        button_info = types.InlineKeyboardButton("Info", callback_data='info')
        markup.add(button_start)
        markup.add(button_help, button_info)
        user_name = message.from_user.first_name
        greet1 = greetings_generator1.get_random_text()
        greet2 = greetings_generator2.get_random_text()
        greeting = f"{greet1}, {user_name}! {greet2}"
        self.bot.send_message(message.chat.id, greeting, reply_markup=markup)

    def send_start_menu_keyboard(self, message):
        """
        Displays a menu with options for learning more about the app, becoming a zoo guardian, or taking a quiz.
        """
        greet2 = greetings_generator2.get_random_text()
        greeting = f"{greet2}"
        markup = types.InlineKeyboardMarkup()
        button_learn_more = types.InlineKeyboardButton("Learn More", callback_data='learn_more')
        button_become_guardian = types.InlineKeyboardButton("Become a Guardian?", callback_data='become_guardian?')
        button_start_quiz = types.InlineKeyboardButton("QUIZ", callback_data='start_quiz')
        markup.add(button_start_quiz)
        markup.add(button_become_guardian, button_learn_more)
        try:
            self.bot.send_message(message.chat.id, greeting)
            logo_greeting = logo_photo
            with open(logo_greeting, 'rb') as logo:
                start_greet = start_generator.get_random_text()
                start_menu_message = f"{start_greet}:"
                self.bot.send_photo(message.chat.id, logo, caption=start_menu_message, reply_markup=markup)

        except FileNotFoundError:
            raise LogoFileNotFoundException("Logo file not found.")
    def send_help_message(self, message):
        """
        Sends a help message containing instructions or information about the bot's functionality.
        """
        help_message = help_text
        self.bot.send_message(message.chat.id, help_message)

    def send_contacts(self, message):
        """
        Sends contact information for the organization or service.
        """
        contacts_message = contacts_text
        self.bot.send_message(message.chat.id, contacts_message)

    def send_info_message(self, message):
        """
        Sends information about the organization or service, including a link to the website.
        """
        info_url = "https://moscowzoo.ru/"
        markup = types.InlineKeyboardMarkup()
        info_button = types.InlineKeyboardButton("Visit Zoo Website", url=info_url)
        markup.add(info_button)
        info_message = info_text
        self.bot.send_message(message.chat.id, info_message, reply_markup=markup)

    def send_become_guardian_info(self, message):
        """
        Provides information about becoming a zoo guardian, including a link to learn more.
        """
        guardian_message = guardian_text
        info_guardian = info_guardian_url
        keyboard = types.InlineKeyboardMarkup()
        button_info_guardian = types.InlineKeyboardButton('Learn About Program', url=info_guardian)
        button_get_contacts = types.InlineKeyboardButton('Contacts', callback_data='contacts')
        keyboard.add(button_info_guardian)
        keyboard.add(button_get_contacts)
        self.bot.send_message(message.chat.id, guardian_message, reply_markup=keyboard)

    def send_start_quiz_message(self, message):
        """
        Starts the quiz for the user.
        """
        self.quiz.start_quiz(message.chat.id)
        self.totem_animal_data = None

    def send_default_response(self, message):
        """
        Sends a default response when no specific action matches the input.
        """
        default_response = default_response_text
        answer = self.bot.send_message(message.chat.id, default_response)
        time.sleep(3)
        self.bot.delete_message(message.chat.id, message.message_id)
        time.sleep(6)
        self.bot.delete_message(message.chat.id, answer.message_id)

    def show_totem_animal_info(self, message):
        """
        Displays information about the user's totem animal after completing the quiz.
        """
        try:
            if not self.totem_animal_data:
                self.result_animal = self.quiz.calculate_results()
                print("Animal determined:", self.result_animal)
                self.totem_animal_data = get_totem_animal_data(self.result_animal)
            animal_data = self.totem_animal_data
            print("Received animal data:", animal_data)
            photo_url = animal_data.get('image_url', '')
            text = f"<b>{animal_data['name']}</b>\n"
            text += f"{animal_data['description']}\n"
            msg = '<b>Results obtained! Move ahead!</b>'
            markup = types.InlineKeyboardMarkup()
            button_continue = types.InlineKeyboardButton('Adventures Continue...', callback_data='continue')
            markup.add(button_continue)
            if photo_url:
                photo = open(photo_url, 'rb')
                self.bot.send_photo(message.chat.id, photo, caption=text, parse_mode='HTML')
                time.sleep(3)
                answer = self.bot.send_message(message.chat.id, msg, reply_markup=markup, parse_mode='HTML')
        except Exception as e:
            error_message = "Take the quiz to receive results."
            answer = self.bot.send_message(message.chat.id, error_message)
            print(f"Error: {e}. Empty results list.")
            time.sleep(3)
            self.bot.delete_message(message.chat.id, answer.message_id)

    def processing_of_results(self, message):
        """
        Shows intermediate steps after completing a quiz before finalizing the user's journey.
        """
        if not self.totem_animal_data:
            self.totem_animal_data = get_totem_animal_data(self.result_animal)
        animal_data = self.totem_animal_data
        website_url = animal_data.get('website_url', '')
        text = '<b>You have come a long way, only one step remains! But choosing is hard...</b>'
        keyboard = types.InlineKeyboardMarkup()
        button_info = types.InlineKeyboardButton("Learn More About Animal", url=website_url)
        button_get_result = types.InlineKeyboardButton('Download Result', callback_data='get_res')
        button_get_res_mail = types.InlineKeyboardButton('A Bit Serious...', callback_data='some_serious')
        button_info_guardian = types.InlineKeyboardButton('Become a Guardian?', callback_data='become_guardian?')
        button_become_guardian = types.InlineKeyboardButton('Become a Guardian!', callback_data='become_a_guardian')
        button_quiz_repeat = types.InlineKeyboardButton("Try Again?", callback_data='start')
        keyboard.row(button_info)
        keyboard.row(button_get_result)
        keyboard.row(button_get_res_mail)
        keyboard.row(button_info_guardian)
        keyboard.row(button_become_guardian)
        keyboard.row(button_quiz_repeat)
        self.bot.send_message(message.chat.id, text, reply_markup=keyboard, parse_mode='HTML')

    def load_result_list(self, message):
        """
        Sends the result list for the user's totem animal.
        """
        if self.result_animal is not None:
            self.bot.send_document(message.chat.id,
                                  document=open(f'./assets/totem_animals/{self.result_animal}.jpg', 'rb'),
                                  caption='Totem Animal')
            time.sleep(2)
            share_result_message = share_result_text
            self.bot.send_message(message.chat.id, share_result_message)
        else:
            answer = self.bot.send_message(message.chat.id, "Result not found.")
            time.sleep(3)
            self.bot.delete_message(message.chat.id, answer.message_id)

    def become_a_guardian(self, message):
        """
        Provides information about becoming a zoo guardian.
        """
        send_message = send_message_text
        self.bot.send_message(message.chat.id, send_message, parse_mode='HTML')

    def some_serious(self, message):
        """
        Sends a message with serious content.
        """
        send_message = serious_text
        self.bot.send_message(message.chat.id, send_message, parse_mode='HTML')

    def agreement(self, message):
        """
        Collects and processes quiz-related user data for potential email notifications.
        """
        try:
            user_id = message.from_user.id
            full_name = f"{message.from_user.first_name} {message.from_user.last_name}"
            user_info = self.quiz.collection_of_information(user_id, full_name)
            subject = 'Quiz Results from Zoo-Bot'
            animal_data = self.totem_animal_data
            results = str({**user_info, **animal_data})
            print(results)
            if send_email(results, subject):
                send_message = 'Sent'
            else:
                send_message = 'Unable to send, try again later'
            self.bot.send_message(message.chat.id, send_message)
        except TypeError:
            send_message = 'Quiz not completed yet, this keyword should be used later'
            answer = self.bot.send_message(message.chat.id, send_message)
            time.sleep(2)
            self.bot.delete_message(message.chat.id, message.message_id)
            time.sleep(4)
            self.bot.delete_message(message.chat.id, answer.message_id)


if __name__ == '__main__':
    """
    Main execution block that initializes the bot manager and starts the bot.
    """
    bot_key = config('AYGO_ZOO_BOT')
    bot_manager = BotManager(bot_key)
    bot_manager.start_bot()