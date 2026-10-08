# Course Service

Kurzuskatalógus és férőhely. A lista és az admin műveletek publikusak, helyet foglalni és felszabadítani az Enroll szolgáltatása tud.

## Publikus végpontok

### `GET /api/courses`

Az összes kurzus.

```json
[{"id": 1, "name": "Analízis 1", "max_capacity": 2, "current_capacity": 0}]
```

### `GET /api/courses/{course_id}`

Egy kurzus.

| Kód | Eredmény |
| --- | --- |
| 200 | A kurzus JSON-ja |
| 404 | Kurzus nem található |

### `POST /api/courses`

Új kurzus, adminnak.

```json
{"name": "Adatbázisok", "max_capacity": 40}
```

| Kód | Eredmény |
| --- | --- |
| 201 | A létrehozott kurzus |
| 422 | Üres név vagy nem pozitív kapacitás |

### `PUT /api/courses/{course_id}`

Módosítás, adminnak. A név és a kapacitás külön is küldhető.

```json
{"name": "Analízis 2", "max_capacity": 50}
```

| Kód | Eredmény |
| --- | --- |
| 200 | A módosított kurzus |
| 400 | A kapacitás kisebb lenne a jelenlegi létszámnál |
| 404 | Kurzus nem található |

### `DELETE /api/courses/{course_id}`

Törlés, adminnak.

| Kód | Eredmény |
| --- | --- |
| 200 | `{"status": "success", "message": "Kurzus törölve."}` |
| 400 | Van feliratkozott hallgató, nem törölhető |
| 404 | Kurzus nem található |

## Belső végpontok

Ezeket az Enroll hívja. Nincs kérés törzs. A foglalás nem tudja túllépni a keretet.

### `POST /internal/courses/{course_id}/reserve`

Egy hely lefoglalása.

| Kód | Eredmény |
| --- | --- |
| 200 | `{"status": "success", "course": {...}}` |
| 400 | A kurzus betelt |
| 404 | Kurzus nem található |

### `POST /internal/courses/{course_id}/release`

Egy hely felszabadítása tárgyleadáskor.

| Kód | Eredmény |
| --- | --- |
| 200 | `{"status": "success", "course": {...}}` |
| 400 | Nincs mit felszabadítani |
| 404 | Kurzus nem található |

## Futtatás

Docker mellett a projekt mappájában: `docker compose up --build`.

Az API a http://localhost:8001 címen van, a felület ugyanezen a címen nyílik meg. A Postgres a gépen az 5433-as porton figyel.

Kész kurzusok: 1, Analízis 1, max 2 fő. 2, Programozás Alapjai, max 30 fő.
