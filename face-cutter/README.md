## face-cutter

Нужно заполнить пустые поля в *config.ini*:\
*aws\_* - статический ключ для хранилища\
*api\_* - API-ключ для Vision
*queue_address* - адрес до самой очереди сообщений

После заполнения *config.ini* нужно все упаковать в ZIP-архив и создать облачную функцию (я делал на *Python 3.9*) через ZIP-архив.\
Точкой входа указать *main.handler*, выбрать сервисный аккаунт и нажать '*Создать версию*'

Затем необходимо создать триггер на создание объектов в хранилище, суффиксом указать *.jpg* и поставить на вызов созданной облачной функции.

После этого можно загрузить в хранилище любую картинку *.jpg*. В этой же папке будут созданы картинки *<имя_картинки>_face-<номер>.jpg*, если на загруженной картинке были лица.