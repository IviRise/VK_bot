import requests
from vk_api import VkApi
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
from geopy.geocoders import Nominatim
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

class Bot:
    def __init__(self, token):
        # Авторизация сессии
        vk_session = VkApi(token=token)
        self.vk = vk_session.get_api()
        self.longpoll: VkLongPoll = VkLongPoll(vk_session)

        self.user_id = None
        self.weather_flag = False

        self.geolocator = Nominatim(user_agent='my_weather_bot') # user_agent — имя проги

        self.message = {
            'старт': ('Привет!'
                      '\nЯ IviBot и я умею показывать погоду 👍'
                      '\nВот мой список команд:'
                      '\n\n💪 /help - помощь'
                      '\n🏙️ /weather [город] - получить погоду'
                      '\n💻 /about - информация о проекте'
                      '\n💡 /fact - интересный факт'
                      '\n\nПРИМЕЧАНИЕ: скобки писать не нужно!'),
            'помощь': ('Список доступных команд:'
                       '\n\n💪 /help - помощь'
                       '\n🏙️ /weather [город] - получить погоду'
                       '\n💻 /about - информация о проекте'
                       '\n💡 /fact - интересный факт'
                       '\n\nПРИМЕЧАНИЕ: скобки писать не нужно!'),
            'привет': 'И тебе привет! 🤝',
            'пока': 'До встречи! 👋',
            'разработчик': ('Привет!'
                            '\nМеня зовут Иван (IviRise).'
                            '\n\nДанный бот был создан в качестве учебного проекта 🙃'
                            '\nМой тг: @ivirise'
                            '\nМой вк: @ivan_ivirise'
                            '\n\nВозможности бота:'
                            '\n\n1. Он умеет определять погоду по названию города.'
                            '\n2. Он умеет выдавать случайный факт :)'
                            '\nНа данном этапе это все...'
                            '\n\nПриятного пользования ботом 😉'),
            'город_не_указан': 'Укажи город, например: /weather Москва',
            'город_не_найден': lambda s: f"Не удалось найти город '{s}'. "
                                         f"Проверь название или попробуй на английском (Moscow).",
            'погода': 'Укажите город! 😉',
            'статистика_заголовок': '📝 Статистика использования бота в городах:\n\n',
            'статистика_город': lambda s, n: f'В городе {s.title()} бот определял погоду {self._n(n)}\n'

        }
        self.emoji = {
            0: '☀️',
            1: '🌤️',
            2: '⛅',
            3: '🌥️',
            45: '🌫️',
            48: '🌫️',
            51: '💧',
            53: '💧',
            55: '💧',
            61: '☔',
            63: '🌦️',
            65: '🌧️',
            71: '⛄',
            73: '⛄',
            75: '⛄',
            80: '🌧️',
            81: '⛈️',
            82: '⛈️',
            95: '⚡',
            96: '⚡❄️',
            99: '⚡❄️'
        }

    def _send(self, text):
        self.vk.messages.send(
            user_id = self.user_id,
            message = text,
            random_id = get_random_id()
        )

    @staticmethod
    def _n(n):
        if 10 <= n % 100 <= 20:
            return f"{n} раз"
        last = n % 10
        if last == 1:
            return f"{n} раз"
        if 2 <= last <= 4:
            return f"{n} раза"
        return f"{n} раз"

    def send_keyboard(self):
        # Создаем объект клавиатуры
        # one_time=False — клавиатура НЕ скроется после нажатия любой кнопки
        keyboard = VkKeyboard(one_time=False)

        # Добавляем первую кнопку. Можно указать цвет.
        # POSITIVE — зеленый, PRIMARY — синий, NEGATIVE — красный, SECONDARY — белый
        # Добавляем вторую кнопку в той же строке (по умолчанию)
        keyboard.add_button('Помощь', color=VkKeyboardColor.POSITIVE)
        # Чтобы добавить кнопку на новой строке, используем метод add_line()
        keyboard.add_line()
        keyboard.add_button('Погода', color=VkKeyboardColor.SECONDARY)
        keyboard.add_line()
        keyboard.add_button('О разработчике', color=VkKeyboardColor.PRIMARY)
        keyboard.add_line()
        keyboard.add_button('Статистика', color=VkKeyboardColor.NEGATIVE)
        keyboard.add_line()
        keyboard.add_button('Факт', color=VkKeyboardColor.NEGATIVE)

        # Отправляем сообщение с клавиатурой
        self.vk.messages.send(
            peer_id=self.user_id,
            message='Чем могу помочь?',
            random_id=get_random_id(),
            keyboard=keyboard.get_keyboard()
        )

    @staticmethod
    def get_url(lat, lon):
        return f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"

    def get_coordinates(self, city_name):
        try:
            location = self.geolocator.geocode(city_name)
            if location:
                return location.latitude, location.longitude
            else:
                return None, None
        except Exception as e:
            print(f"Ошибка геокодирования: {e}")
            return None, None

    def get_weather(self, city):
        # Получаем координаты
        latitude, longitude = self.get_coordinates(city)
        if latitude is None or longitude is None:
            self._send(self.message['город_не_найден'](city))
            return
        try:
            # Получаем валидную ссылку
            url = self.get_url(latitude, longitude)
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()  # Выбросит исключение при плохом статусе
            data = resp.json()

            with open('statistic.txt', 'a', encoding='utf-8') as f:
                f.write(city + '\n')

            current = data.get('current_weather')
            if not current:
                raise ValueError('Нет данных о погоде')
            answer = (f'{self.emoji[current['weathercode']]}Погода\n'
                      f'🏢 Город: {city}\n'
                      f'🌡️ Температура: {current['temperature']}°C\n'
                      f'🌪️ Скорость ветра: {current['windspeed']} км/ч')
        except requests.exceptions.RequestException as e:
            print(f'Ошибка запроса: {e}')
            answer = 'Ошибка соединения с сервером погоды. Попробуй позже.'
        except (KeyError, ValueError) as e:
            print(f'Ошибка парсинга: {e}')
            answer = 'Не удалось получить погоду. Проверь название города или попробуй позже.'

        self._send(answer)

    def get_statistic(self):
        city_statistic = {}
        try:
            with open('statistic.txt', encoding='utf-8') as f:
                lines = f.readlines()
        except FileNotFoundError:
            self._send("📊 Статистика пока пуста. Никто ещё не спрашивал погоду.")
            return
        for line in lines:
            this_city = line.strip()
            if this_city in city_statistic:
                city_statistic[this_city] += 1
            else:
                city_statistic[this_city] = 1
        message = self.message['статистика_заголовок']
        for city in city_statistic:
            message += self.message['статистика_город'](city, city_statistic[city])
        self._send(message)
        # print(city_statistic)

    @staticmethod
    def get_random_fact():
        try:
            url = f"https://meowfacts.herokuapp.com/?lang=rus"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                fact = response.json()['data'][0]
                return fact
            else:
                return "Не удалось получить факт, попробуй позже."
        except Exception as e:
            return f"Ошибка: {e}"

    def start(self):
        print('Бот запущен. Ожидаю сообщения...')
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                # Получили новое сообщение в диалог с ботом
                msg = event.text.lower().strip()
                self.user_id = event.user_id

                # Основные команды
                match msg:
                    case '/start':
                        self._send(self.message['старт'])
                        self.send_keyboard()
                    case '/help':
                        self._send(self.message['помощь'])
                        self.send_keyboard()
                    case '/about':
                        self._send(self.message['разработчик'])
                    case '/statistic':
                        self.get_statistic()
                    case '/fact':
                        self._send(self.get_random_fact())
                    case 'привет':
                        self._send(self.message['привет'])
                        self.send_keyboard()
                    case 'пока':
                        self._send(self.message['пока'])
                    # События с клавиатуры
                    case 'помощь':
                        self._send(self.message['помощь'])
                    case 'о разработчике':
                        self._send(self.message['разработчик'])
                    case 'статистика':
                        self.get_statistic()
                    case 'факт':
                        self._send(self.get_random_fact())

                # Погода
                if msg.startswith('/weather'):
                    try:
                        city = msg.strip().split(maxsplit=1)[1]
                    except IndexError:
                        self._send(self.message['город_не_указан'])
                        continue
                    self.get_weather(city)
                elif msg == 'погода':
                    self.weather_flag = True
                    self._send(self.message['погода'])

                elif self.weather_flag:
                    city = msg.strip()
                    self.get_weather(city)
                    self.weather_flag = False

# Токен
with open('token.txt', 'r') as f:
    TOKEN = f.read().strip()

if __name__ == '__main__':
    vk_bot = Bot(TOKEN)
    vk_bot.start()