Abills payments
=================

Свободный протокол для общения с БД Abills для пополнения Internet через терминалы самообслуживания

Настройка
--------------------------
в файле dbmanager.py ввести параметры для доступа в БД Abills
```
_cfg = {
    'host':'127.0.0.1',
    'user':'payments',
    'pwd':'password',
    'db':'abills'
}
```

в файлах **privat.py**, **globalmoney.py**,**qiwi.py** ввести в поле _operator_ ИД оператора от имени которого будут заносится данные в БД

Дополнительно в **privat.py** заполнить параметры:

```
company_id = ''
company_name = ''
company_message = ''
```

Дополнительно в **globalmoney.py** внести параметр: _secret_

Настроить Web-сервер. Сделать тестовые платежи
