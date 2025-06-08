import time

from telebot import types

from service import (load_quiz_data, choice, best_matching)

from textinfo import result_text, logo_end_photo, logo_start_quiz_photo


class Quiz:
    def __init__(self, bot):
        """
        Initializes the Quiz class with the provided Telegram bot instance.
        Sets up necessary attributes for managing quiz questions, user responses, and results.
        """
        self.result_tuples = None
        self.user_responses = []
        self.bot = bot
        self.questions = self.load_quiz_data()
        self.current_question_index = 0
        self.answers = []
        self.message_id = None
        self.current_question_text = None

    @staticmethod
    def create_answer_markup(answers):
        """
        Creates an inline keyboard markup for displaying answer options.
        """
        markup = types.InlineKeyboardMarkup(row_width=1)
        for i, answer in enumerate(answers, start=1):
            button_text = answer["text"]
            button_data = f"answer_{i}"
            button = types.InlineKeyboardButton(button_text, callback_data=button_data)
            markup.add(button)
        return markup

    @staticmethod
    def create_result_keyboard():
        """
        Creates an inline keyboard for showing results and restarting the quiz.
        """
        keyboard = types.InlineKeyboardMarkup()
        result_button = types.InlineKeyboardButton("View Result", callback_data="show_result")
        restart_button = types.InlineKeyboardButton("Restart Quiz", callback_data='restart_quiz')
        keyboard.add(result_button, restart_button)
        return keyboard

    @staticmethod
    def load_quiz_data():
        """
        Loads quiz data from a file.
        """
        file_name = 'Questions'
        return load_quiz_data(file_name)

    def calculate_results(self):
        """
        Calculates the final result based on user answers.
        """
        first_ranks = self.answers[:5]
        last_ranks = self.answers[5:]
        self.result_tuples = [round((first_ranks[i] + last_ranks[i]) / 2, 1) for i in range(5)]
        print(self.result_tuples)
        chosen_animal = best_matching(self.result_tuples, choice)
        return chosen_animal

    def collection_of_information(self, user_id, full_name):
        """
        Collects user information and quiz results for potential email notifications.
        """
        user_info = {
            'user_id': user_id,
            'full_name': full_name,
            'user_responses': self.user_responses,
            'results': self.result_tuples,
        }
        return user_info

    def end_quiz(self, chat_id):
        """
        Ends the quiz and displays the result message with an option to view the result or restart the quiz.
        """
        result_message = result_text
        logo_end = logo_end_photo
        with open(logo_end, "rb") as photo:
            self.bot.send_photo(chat_id, photo, caption=result_message,
                                reply_markup=self.create_result_keyboard(), parse_mode='HTML')


    def start_quiz(self, chat_id):
        """
        Starts the quiz by resetting the question index and answers, then sends the first question.
        """
        self.current_question_index = 0
        self.answers = []
        logo_start_quiz = logo_start_quiz_photo
        with open(logo_start_quiz, "rb") as photo:
            self.bot.send_photo(chat_id, photo)
            time.sleep(3)
        self.send_question(chat_id)



    def send_question(self, chat_id):
        """
        Sends the next question in the quiz sequence.
        """
        if self.current_question_index < len(self.questions):
            image_number = self.current_question_index + 1
            image_path = f'assets/Eng/logo_quiz_{image_number}.jpg'
            with open(image_path, 'rb') as image_file:
                self.bot.send_photo(chat_id, image_file)
                time.sleep(6)
            question_data = self.questions[self.current_question_index]
            self.current_question_text = question_data['question']
            markup = self.create_answer_markup(question_data["answers"])
            message = self.bot.send_message(chat_id, self.current_question_text,
                                           reply_markup=markup, parse_mode='Markdown')
            self.message_id = message.message_id
        else:
            self.end_quiz(chat_id)



    def process_answer(self, chat_id, answer_num):
        """
        Processes the user's answer to a question, updates the answer list, and sends the next question.
        """
        rank = self.questions[self.current_question_index - 1]["answers"][answer_num - 1]["rank"]
        self.answers.append(rank)
        self.current_question_index += 1
        print(f'Answered question {self.current_question_index}: Rank {rank}')
        selected_answer = self.questions[self.current_question_index - 1]["answers"][answer_num - 1]["text"]
        response_message = f"{self.current_question_text}\nYour Answer: {selected_answer}"
        self.user_responses.append(response_message)
        print(self.user_responses)
        self.bot.send_message(chat_id, response_message, parse_mode='Markdown')
        if self.message_id:
            self.bot.delete_message(chat_id, self.message_id)
        self.send_question(chat_id)