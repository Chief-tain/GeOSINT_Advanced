from aiogram.utils import markdown


START_MESSAGE = \
markdown.bold("🫡 Здравия желаю!\n") \
+ "\n" \
"Перечень моих возможностей:\n" \
"\- Создание интерактивной карты;\n" \
"\- Создание тематической интерактивной карты;\n" \
"\- Создание общей информационно\-новостной сводки;\n" \
"\- Создание краткой информационно\-новостной сводки по населенному пункту;\n" \
"\- Создание информационно\-отчетных документов\.\n" \
"\n" \
+ markdown.bold("GeOSINT Service к Вашим услугам...")  +\
"\n\n" +\
markdown.bold("❓ По вопросам работы бота и (или) сотрудничества: @Chief_train\n")


HELP_MESSAGE =  \
markdown.bold("GeOSINT Service работает в нескольких режимах:\n") \
+ "\n" \
+ markdown.bold("1. Режим создания интерактивной карты:\n") +\
"Бот получает границы временного интервала и создает интерактивную карту\.\n" \
+ markdown.bold("Команда: /map\n") + \
"\n" \
+ markdown.bold("2. Режим создания тематической интерактивной карты:\n") +\
"Бот получает границы временного интервала и ключевое слово, затем создает интерактивную карту по ключевому слову и семантически близким к нему\.\n" \
+ markdown.bold("Команда: /tag_map\n") + \
"\n" \
+ markdown.bold("3. Режим создания общей информационно-новостной сводки:\n") +\
"Бот получает границы временного интервала и создает краткую информационно\-новостную сводку\.\n" \
+ markdown.bold("Команда: /fast_summary\n") + \
"\n" \
+ markdown.bold("4. Режим создания краткой новостной сводки по населенному пункту:\n") +\
"Бот получает границы временного интервала и название насенного пункта, затем создает краткую информационно\-новостную сводку по выбранному населенному пункту\.\n" \
+ markdown.bold("Команда: /city_summary\n") + \
"\n" \
+ markdown.bold("5. Режим создания информационно-отчетного документа:\n") +\
"Бот получает границы временного интервала создает информационно\-отчетный документ\.\n" \
+ markdown.bold("Команда: /report\n") + \
"\n" \
+ markdown.bold("GeOSINT Service к Вашим услугам...") +\
"\n\n" +\
markdown.bold("❓ По вопросам работы бота и (или) сотрудничества: @Chief_train\n")

CHANGE_MODE_MESSAGE = '🌍 Вы перешли в режим создания {}\!'

WRONG_MODE_MESSAGE = '❌ Максимальный размер временного интервала \- 31 день\.\.\.'

WRONG_MODE_MESSAGE_3 = '❌ Максимальный размер временного интервала \- 3 дня\.\.\.'

NOT_ENOUGHT_INFO_MESSAGE = '❌ Недостаточно информации по данному населенному пункту для составления краткой новостной сводки\.\.\.'

WRONG_TAG_MESSAGE = '❌ К сожалению, данное слово GeOSINT Service неизвестно\.\.\.'

WRONG_CITY_MESSAGE = '❌ К сожалению, данный населенный пункт GeOSINT Service неизвестен\.\.\.'

PLEASE_WAIT = markdown.bold("⌛ Подготовка ответа...\n")

DATE_INPUT_MESSAGE = '▶️ Выберите границы временного интервала: ⛔️'

INPUT_FROM_CALENDAR = markdown.bold("⏱ Вы выбрали: ") + '{}'

BEGIN_INPUT_MESSAGE = '▶️ Выберите начало временного интервала:\n'

END_INPUT_MESSAGE = '🛑 Выберите конец временного интервала:\n'

PICK_CHANNELS = markdown.bold('Выберите источники информации:')

PARAPHRASE_MESSAGE = '🔮 Из {} информационно\-новостных сообщений было выделено {} наиболее информативных, по ним составлена следующая новостная сводка:\n'

MAP_CAPTION = markdown.bold("📑 Тип документа: ") + '{}\n' \
            + markdown.bold("▶️ Начало: ") + '{}\n' \
            + markdown.bold("⛔️ Конец: ") + '{}\n' \
            + markdown.bold("📍 Отмечено событий: ") + '{}\n\n' \
            + markdown.bold("❓ По вопросам работы бота и (или) сотрудничества: @Chief_train\n")

REGION_MAP_CAPTION = markdown.bold("📑 Тип документа: ") + '{}\n' \
                    + markdown.bold("🌏 Выбранные регионы: ") + '\n{}\n' \
                    + markdown.bold("▶️ Начало: ") + '{}\n' \
                    + markdown.bold("⛔️ Конец: ") + '{}\n' \
                    + markdown.bold("🔈 Источники информации: ") + '{}\n' \
                    + markdown.bold("📍 Отмечено событий: ") + '{}\n\n' \
                    + markdown.bold("❓ По вопросам работы бота и (или) сотрудничества: @Chief_train\n")

TAG_MAP_CAPTION = markdown.bold("📑 Тип документа: ") + '{}\n' \
                    + markdown.bold("🔑 Ключевое слово: ") + '{}\n' \
                    + markdown.bold("▶️ Начало: ") + '{}\n' \
                    + markdown.bold("⛔️ Конец: ") + '{}\n' \
                    + markdown.bold("📍 Отмечено событий: ") + '{}\n\n' \
                    + markdown.bold("❓ По вопросам работы бота и (или) сотрудничества: @Chief_train\n")

TAG_LIST_CAPTION = markdown.bold("📑 Тип документа: ") + '{}\n' \
                    + markdown.bold("🔑 Ключевое слово: ") + '{}\n' \
                    + markdown.bold("▶️ Начало: ") + '{}\n' \
                    + markdown.bold("⛔️ Конец: ") + '{}\n' \
                    + markdown.bold("🔈 Источники информации: ") + '{}\n' \
                    + markdown.bold("📍 Отмечено событий: ") + '{}\n\n' \
                    + markdown.bold("❓ По вопросам работы бота и (или) сотрудничества: @Chief_train\n")

TAG_INPUT_MESSAGE = '🔑 Введите тег \(одно ключевое слово\):\n' + markdown.bold("⌨️ Пример: Взрыв")

CITY_INPUT_MESSAGE = '🔑 Введите название населенного пункта:\n' + markdown.bold("⌨️ Пример: Донецк")

CITIES_INPUT_MESSAGE = '✅ Введите названия областей \(каждое на новой строке\), информация по которым будет нанесена на карту:\n' \
                        + markdown.bold("📋 Перечень областей: /region_list") + '\n' \
                        + markdown.bold("⌨️ Пример:") + '\n'\
                        + 'Донецкая область' + '\n' \
                        + 'Харьковская область' + '\n' \
                        + 'Одесская область'
                        

TOTAL_POINTS_MESSAGE = "🌐 На карте будет отмечено {} событие\(ий\)\."

TOTAL_TAGS_MESSAGE = "🔝 Наиболее близкие слова к '{}' по семантике:\n {}\."

FAST_NEWS_MESSAGE = '🧠 {} информационно\-новостных сообщения были разделены на {} категорий:'

CATEGORY_MESSAGE = \
markdown.bold("#️⃣ Категория: ") + '{}\n' +\
markdown.bold("🔑 Ключевые слова: ") + '{}\n' + \
markdown.bold('📍 Количество информационно-новостных сообщений: ')  + '{}\n' + \
markdown.bold("🔗 Ссылки на источники:") + '\n{}\n{}\n{}'

CHOOSE_CHANNELS_MESSAGE = markdown.bold("🔈 Выберите источники информации: ")

MODE_SWITCH_MESSAGE = 'User {} switched to {}...'

COMMAND_ENTER_MESSAGE = 'User {} asked for {} command...'

DATA_ENTER_MESSAGE = 'User {} entered {}...'

REGION_LIST_MESSAGE = markdown.bold("📋Перечень областей:\n") + \
                        '\- Автономная Республика Крым;\n' \
                        '\- Винницкая область;\n' \
                        '\- Волынская область;\n' \
                        '\- Днепропетровская область;\n' \
                        '\- Донецкая область;\n' \
                        '\- Житомирская область;\n' \
                        '\- Закарпатская область;\n' \
                        '\- Запорожская область;\n' \
                        '\- Ивано\-Франковская область;\n' \
                        '\- Киевская область;\n' \
                        '\- Кировоградская область;\n' \
                        '\- Луганская область;\n' \
                        '\- Львовская область;\n' \
                        '\- Николаевская область;\n' \
                        '\- Одесская область;\n' \
                        '\- Полтавская область;\n' \
                        '\- Ровенская область;\n' \
                        '\- Сумская область;\n' \
                        '\- Тернопольская область;\n' \
                        '\- Харьковская область;\n' \
                        '\- Херсонская область;\n' \
                        '\- Хмельницкая область;\n' \
                        '\- Черкасская область;\n' \
                        '\- Черниговская область;\n' \
                        '\- Черновицкая область\.'

ADMIN_MESSAGE = markdown.bold("Date: ") + '{}\n' + \
                markdown.bold("User name: ") + '{}\n' + \
                markdown.bold("User ID: ") + '{}\n' + \
                markdown.bold('User action: ')  + '{}\n' + \
                markdown.bold('Begin: ')  + '{}\n' + \
                markdown.bold('End: ')  + '{}\n' + \
                markdown.bold('Channels: ')  + '{}\n' + \
                markdown.bold("Extra info: ") + '{}'

CHECK_MESSAGE = markdown.bold("Last DB update: ") + '{}\n' \
                + markdown.bold("RU records: ") + '{}\n' \
                + markdown.bold("UA records: ") + '{}\n' \
                + markdown.bold("Amount of actions: ") + '{}'
                