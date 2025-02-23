# File Storage API

## Endpoints

### User Management
- **POST** `/api/admin/users/create`: Создание пользователя сервиса.

### File Management
- **POST** `/api/files/upload`: Загрузка файла.
- **GET** `/api/files/{file_id}/download`: Скачивание файла.
- **GET** `/api/files/changes`: Получение списка изменений.
- **POST** `/api/files/{filename}/update`: Обновление файла.

## Usage
- Для доступа к API используйте токены, выданные при создании пользователей.
- Управление файлами доступно через веб-интерфейс по адресу `/`.

## Future Enhancements
- Расширение системы ролей и разрешений.
- Интеграция с брокером сообщений для обработки событий.
- Улучшение веб-интерфейса для управления файлами.