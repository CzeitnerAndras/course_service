# Course Service

## Api
### GET /api/courses
* Lekéri az összes kurzust
* Válaszba JSON-t ad pl: [{"id": 1, "name": "Analízis 1", "max_capacity": 2, "current_capacity": 1}]

### GET /api/courses/{course_id}
* Lekér egy kurzust
* JSON-t ad vissza pl: {"id": 1, "name": "Analízis 1", "max_capacity": 2, "current_capacity": 1}
#### * Válaszok:
* 200 Sikeres
* 404 Not Found: Kurzus nem található

### POST /api/courses
* Új kurzus létrehozása (admin)
* Kérés inputja JSON pl: {"name": "Adatbázisok", "max_capacity": 40}
#### * Válaszok:
* 201 Created: a létrehozott kurzus JSON-ja
* 422 Validációs hiba (üres név / nem pozitív kapacitás)

### PUT /api/courses/{course_id}
* Kurzus módosítása (admin), a mezők külön is megadhatók
* Kérés inputja JSON pl: {"name": "Analízis 2", "max_capacity": 50}
#### * Válaszok:
* 200 Sikeres: a módosított kurzus JSON-ja
* 400 Bad Request: A kapacitás nem lehet kisebb a jelenlegi létszámnál
* 404 Not Found: Kurzus nem található

### DELETE /api/courses/{course_id}
* Kurzus törlése (admin)
#### * Válaszok:
* 200 Sikeres {"status": "success", "message": "Kurzus törölve."}
* 400 Bad Request: A kurzusnak van feliratkozott hallgatója, nem törölhető
* 404 Not Found: Kurzus nem található

### POST /internal/courses/{course_id}/reserve
* Belső végpont az Enrollnak: egy hely lefoglalása
#### * Válaszok:
* 200 Sikeres {"status": "success", "course": {...}}
* 400 Bad Request: Sikertelen tárgyfelvétel: A kurzus betelt!
* 404 Not Found: Kurzus nem található

### POST /internal/courses/{course_id}/release
* Belső végpont az Enrollnak: egy hely felszabadítása tárgyleadáskor
#### * Válaszok:
* 200 Sikeres {"status": "success", "course": {...}}
* 400 Bad Request: Nincs mit felszabadítani
* 404 Not Found: Kurzus nem található