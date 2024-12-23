# Project3_python
# Weather Route Checker
---

### **Обработанные ошибки**

1. **Ошибки ввода данных пользователем**
   - Описание: Пользователь может ввести некорректное название города, пустую строку или случайный текст.
   - Решение:
     - Проверка наличия данных в форме: если одно из полей формы пустое, то возвращается сообщение об ошибке.
     - Проверка существования города с использованием API. Если город не найден, пользователю отображается сообщение:  
       *"Город [название] не найден. Проверьте правильность ввода."*
   - Влияние на систему: Приложение продолжает работать, пользователь правит ввод

2. **Ошибки API AccuWeather**
   - Описание: Недоступен API-ключ или превышен лимит запросов.
   - Решение:
     - Если API вернул ошибку `401 Unauthorized`, пользователю отображается сообщение:  
       *"Ошибка API: Неверный API-ключ или превышен лимит запросов."*
     - Если API недоступно (`500 Internal Server Error`), пользователь получает сообщение:  
       *"Ошибка API: Сервер временно недоступен. Попробуйте позже."*
   - Влияние на систему: Приложение временно является недоступным для повторного использования
---

## Пример сценария обработки ошибки
1. **Сценарий 1: Некорректный ввод города**
   - Пользователь вводит "Город123".
   - Приложение делает запрос к API и возвращает сообщение:  
     *"Город Город123 не найден. Проверьте правильность ввода."*
   - Пользователь исправляет ввод и повторяет действие.

2. **Сценарий 2: Превышен лимит запросов API**
   - Пользователь делает множество запросов, превышая лимит.
   - Приложение возвращает сообщение:  
     *"Ошибка API: Неверный API-ключ или превышен лимит запросов."*
   - Пользователь ожидает следующий день для сброса лимита.
