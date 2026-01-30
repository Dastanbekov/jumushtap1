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


USERS/ME
1. Если зашел WORKER
Фронтенд делает GET /api/v1/auth/me/ с токеном работника. Response (200 OK):

JSON
{
    "id": 1,
    "email": "worker@example.com",
    "phone": "+996700123456",
    "user_type": "worker",
    "full_name": "Aitmyrza Dastanbekov" 
}
(Поле full_name пришло из таблицы WorkerProfile)

2. Если зашел BUSINESS
Фронтенд делает GET /api/v1/auth/me/ с токеном бизнеса. Response (200 OK):

JSON
{
    "id": 2,
    "email": "ceo@techcompany.kg",
    "phone": "+996555987654",
    "user_type": "business",
    
    // Поля из BusinessProfile:
    "company_name": "Super Tech LLC",
    "bin": "123456789012",
    "inn": "10203040506070",
    "legal_address": "г. Бишкек, пр. Чуй 123",
    "contact_name": "Менеджер Айгуль",
    "contact_number": "+996312111222"
}
3. Если зашел INDIVIDUAL
Фронтенд делает GET /api/v1/auth/me/ с токеном физлица. Response (200 OK):

JSON
{
    "id": 3,
    "email": "ivanov@gmail.com",
    "phone": "+996777112233",
    "user_type": "individual",
    
    // Поля из IndividualProfile:
    "full_name_ru": "Иванов Иван Иванович"
}