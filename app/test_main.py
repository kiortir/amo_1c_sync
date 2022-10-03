from cgi import test
from unicodedata import name
from fastapi.testclient import TestClient

from querystring_parser import parser

try:
    from .main import app
except ImportError:
    from main import app

client = TestClient(app)

DUMMY_HOOK = {
    "leads": {
        "status": {
            "0": {
                "id": "25399013",
                "name": "Lead title",
                "old_status_id": "7039101",
                "status_id": "142",
                "price": "0",
                "responsible_user_id": "123123",
                "last_modified": "1413554372",
                "modified_user_id": "123123",
                "created_user_id": "123123",
                "date_create": "1413554349",
                "account_id": "7039099",
                "custom_fields": [{
                    "id": "427183",
                    "name": "Checkbox custom field",
                    "values": ["1"]
                },
                    {
                    "id": "427271",
                    "name": "Date custom field",
                    "values": ["1412380800"]
                },
                    {
                    "id": "1069602",
                    "name": "Checkbox custom field",
                    "values": ["0"]
                },
                    {
                    "id": "427661",
                    "name": "Text custom field",
                    "values": ["Валера"]
                },
                    {
                    "id": "1075272",
                    "name": "Date custom field",
                    "values": ["1413331200"]
                }
                ]
            }
        }
    }
}


DH3 = {'leads': {'update': [{'id': '6681281', 'name': 'test 2022-09-28', 'status_id': '50200276', 'old_status_id': '50367064', 'price': '0', 'responsible_user_id': '2666554', 'last_modified': '1664815643', 'modified_user_id': '2666554', 'created_user_id': '2666554', 'date_create': '1664366410', 'pipeline_id': '5711290', 'account_id': '30348370', 'custom_fields': [{'id': '480491', 'name': 'Администратор', 'values': [{'value': 'Администратор Мира', 'enum': '313979'}]}, {'id': '480951', 'name': 'Сегмент', 'values': [{'value': 'семейный', 'enum': '314271'}]}, {'id': '480957', 'name': 'Сумма задатка', 'values': [{'value': '10000'}]}, {'id': '490537',
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              'name': 'Бонусная карта', 'values': [{'value': 'да', 'enum': '322101'}]}, {'id': '480665', 'name': 'Баня', 'values': [{'value': 'Каменная на Мира', 'enum': '314099'}]}, {'id': '480671', 'name': 'Дата и время заезда', 'values': ['1664372700']}, {'id': '480679', 'name': 'Дата и время выезда', 'values': ['1664375400']}, {'id': '480683', 'name': 'Количество гостей', 'values': [{'value': '1'}]}, {'id': '480685', 'name': 'Количество детей до 7 лет', 'values': [{'value': '0'}]}], 'created_at': '1664366410', 'updated_at': '1664815643'}]}, 'account': {'subdomain': 'usadbavip', 'id': '30348370', '_links': {'self': 'https://usadbavip.amocrm.ru'}}}


def test_read_main():
    response = client.post("/hook",
                           data=DH3)
    # assert response.status_code == 200
    # assert response.json() == {"msg": "Hello World"}
    print(response.json())


if __name__ == '__main__':
    test_read_main()
