## face-bot

1. Создать Telegram-бота с помощью *@BotFather* и получить его токен.

2. Заполнить пустые поля в *config.ini*:\
*aws\_* - статический ключ для хранилища\
*bucket_name* - имя бакета\
*db_file* - название .json файла из бакета с базой данных\
*bot_token* - токен Telegram-бота
*chat_id* - id пользователя, которому будет писать id (можно узнать через бота *@getidsbot*)

3. После заполнения *config.ini* нужно все упаковать в ZIP-архив и создать облачную функцию (я делал на *Python 3.9*) через ZIP-архив.\
Точкой входа указать *main.handler*, выбрать сервисный аккаунт и нажать '*Создать версию*'.

4. Сделать функцию публичной и отправить запрос *https://api.telegram.org/bot{ТОКЕН_БОТА}/setWebHook?url={ССЫЛКА_НА_ФУНКЦИЮ}* - создатся webhook на функцию.

5. Создать триггер на появление сообщений в очереди и указать вызываемой созданную функцию.

6. Загрузить картинку с лицами через [cloudphoto](https://github.com/schastlivcev/cloud-technologies/tree/master/cloudphoto) (задание 1) и дождаться сообщений в очереди из [face-cutter](https://github.com/schastlivcev/cloud-technologies/tree/master/face-cutter) (задание 2).