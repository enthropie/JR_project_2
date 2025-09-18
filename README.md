**Сервер изображений**

**Запуск приложения:**

1. docker-compose build
2. docker-compose up
3. Приложение доступно в браузере по адресу http://localhost:8000/, pgadmin - http://localhost:8080/

**Резервное копирование данных:**

Снять бекап на windows через powershell хостовой машины с docker:
cd [в_папку_проекта]
docker exec -t image_server_db pg_dump -U postgres images_db > ".\backups\backup_$(Get-Date -Format yyyy-MM-dd_HHmmss).sql"

Альтернатива для других ОС: запустить файл backup.sh

**Документация и ТЗ:**

https://drive.google.com/file/d/1ro605PYMKynE-iFXWi0-zVGISjgIOo7N/view