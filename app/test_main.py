from cgi import test
from unicodedata import name
from fastapi.testclient import TestClient

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

def test_read_main():
    response = client.post("/hook",
                           json=DUMMY_HOOK)
    # assert response.status_code == 200
    # assert response.json() == {"msg": "Hello World"}
    print(response.json())


if __name__ == '__main__':
    test_read_main()
