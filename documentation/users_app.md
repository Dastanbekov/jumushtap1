the ways will return this kinda things - 
Теперь на эндпоинт POST /api/users/register/ ты будешь слать такой JSON (например, для Business):

registration - what we send.
JSON
{
    "email": "corp@example.com",
    "password": "strongpassword123",
    "phone": "+996700123456",
    "user_type": "business",
    "profile": {
        "company_name": "Too Big Tech",
        "bin": "123456789012",
        "inn": "12345678901234",
        "legal_address": "Bishkek, Chuy 1",
        "contact_name": "Aitmyrza",
        "contact_number": "+996555987654"
    }
}
А для Worker:

JSON
{
    "email": "worker@example.com",
    "password": "pass",
    "phone": "+996700111222",
    "user_type": "worker",
    "profile": {
        "full_name": "Ivan Ivanov"
    }
}
