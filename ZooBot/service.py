import random
import os
import smtplib

from decouple import config
from email.mime.text import MIMEText

# parameters of totem animals
# 1 size - small, medium, big
# 2 area of living - can walk, can swim, can fly
# 3 speed - slow, medium, fast
# 4 uniqueness - extinct, rare, common
# 5 food - herbivore, omnivore, carnivore
choice = {
    (3, 2, 1, 2, 2): 'steller_sea_lion',
    (2, 1, 3, 2, 3): 'bobcat',
    (1, 2, 3, 3, 2): 'otter',
    (1, 1, 1, 3, 1): 'chinchilla',
    (1, 1, 3, 2, 1): 'dipodidae',
    (1, 3, 2, 3, 2): 'bat',
    (1, 1, 3, 1, 3): 'manul',
    (2, 1, 3, 1, 3): 'leopard',
    (2, 1, 2, 1, 2): 'orangutan',
    (3, 1, 1, 2, 1): 'elephant',
    (3, 2, 3, 2, 3): 'polar_bear',
    (2, 1, 2, 2, 1): 'alpaca',
    (1, 1, 3, 3, 2): 'raccoon',
    (3, 1, 2, 1, 1): 'musk_ox'
}

def best_matching(user_params, choices):
    """
    Finds the best matching totem animal based on user parameters.
    """
    best_match = None
    min_difference = float('inf')
    for params, animal in choices.items():
        difference = sum(abs(user_param - param) for user_param, param in zip(user_params, params))
        if difference < min_difference:
            min_difference = difference
            best_match = animal
    return best_match

def get_totem_animal_data(anim_name):
    """
    Retrieves information about a totem animal from a file.
    """
    file_path = os.path.join("assets/totem_animals", f"{anim_name.lower()}")
    if not os.path.isfile(file_path):
        return f"No data available for totem animal {anim_name}."
    animal_info = {}
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            key, value = line.strip().split(": ", 1)
            animal_info[key] = value
    return animal_info

def load_quiz_data(quiz_data):
    """
    Loads quiz data from a file.
    """
    file_path = os.path.join("assets/quiz-questions", f"{quiz_data.lower()}")
    if not os.path.isfile(file_path):
        return f"File {quiz_data} not found."
    questions = []
    with open(file_path, 'r', encoding='utf-8') as file:
        question_data = {}
        is_question = False
        for line in file:
            line = line.strip()
            if line.startswith("question:"):
                is_question = True
                if question_data:
                    questions.append(question_data)
                question_data = {"question": line.split(": ", 1)[1]}
            elif line.startswith("answers:"):
                is_question = False
                answers = []
                for ans in line.split(": ")[1].split("; "):
                    answer_number, ans_text_rank = ans.split(". ")
                    ans_text, rank = ans_text_rank.split(":")
                    answers.append({
                        "number": int(answer_number),
                        "text": ans_text.strip(),
                        "rank": float(rank.strip())
                    })
                question_data["answers"] = answers
            elif is_question:
                question_data["question"] += "\n" + line
        if question_data:
            questions.append(question_data)
    return questions

def send_email(results, subject):
    """
    Sends an email with the provided results and subject.
    """
    sender = config('GMAIL_USER')
    password = config('GMAIL_KEY_PYTHON')
    recipient = 'MAILRU_USER'

    msg = MIMEText(results)
    msg['Subject'] = subject
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:  # connect to SMTP server
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, recipient, msg.as_string())
            print('Success!')
            return True
    except Exception as e:
        print(f'{e}\nPlease check your login or password.')
        return False




class RandomTextGenerator:
    def __init__(self, file_path):
        """
        Initializes the RandomTextGenerator with the path to a text file.
        """
        self.file_path = file_path
        self.text_list = self.read_text_from_file()

    def get_random_text(self):
            if not self.text_list:
                return f"File '{self.file_path}' is empty."
            random_text = random.choice(self.text_list)
            return random_text.strip()

    def read_text_from_file(self):
        """
        Reads text from the specified file and returns a list of lines.
        """
        if not os.path.isfile(self.file_path):
            print(f"Warning: File '{self.file_path}' does not exist.")
            return []
        with open(self.file_path, 'r', encoding='utf-8') as file:
            text_list = file.readlines()
        return text_list




greetings_generator1 = RandomTextGenerator('settings/greetings/greet1_list')
greetings_generator2 = RandomTextGenerator('settings/greetings/greet2_list')
start_generator = RandomTextGenerator('settings/start_list')