#!/bin/bash

# Имя контейнера с Postgres
CONTAINER="image_server_db"

# Имя базы данных
DB_NAME="images_db"

# Пользователь Postgres
DB_USER="postgres"

# Папка для хранения бэкапов (локальная, смонтирована в docker-compose)
BACKUP_DIR="./backups"

# Формируем имя файла с датой и временем
TIMESTAMP=$(date +"%Y-%m-%d_%H%M%S")
FILENAME="backup_${TIMESTAMP}.sql"

# Запускаем pg_dump внутри контейнера и сохраняем файл на хосте
docker exec -t $CONTAINER pg_dump -U $DB_USER $DB_NAME > "${BACKUP_DIR}/${FILENAME}"

echo "Бэкап сохранён: ${BACKUP_DIR}/${FILENAME}"
