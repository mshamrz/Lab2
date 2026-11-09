# Лабораторна робота 9: Spry on Google Cloud (and what it would cost)

**Студентка:** Маріана Мороз (`m.moroz.pn@ucu.edu.ua`)  
**GCP Project ID:** `spry-auth`  
**Регіон GCP:** `us-central1`  
**Репозиторій проєкту:** [mshamrz/Lab2](https://github.com/mshamrz/Lab2)  
**Архітектурне рішення:** [docs/adr/0008-gcp-service-choices.md](https://github.com/mshamrz/Lab2/blob/main/docs/adr/0008-gcp-service-choices.md)  
**Terraform конфігурація:** [gcp/](https://github.com/mshamrz/Lab2/tree/main/gcp)

---

## Part 1 — Вибір сервісів Google Cloud для Spry (ADR)

Повний текст архітектурного рішення зафіксовано в [`docs/adr/0008-gcp-service-choices.md`](file:///C:/Users/LEGION/Documents/GitHub/Lab2/docs/adr/0008-gcp-service-choices.md).

### Зведена таблиця відповідності компонентів Spry (AWS vs GCP)

| Компонент Spry | AWS (Labs 1–7) | Google Cloud (Lab 9) | Рішення | Обґрунтування вибору |
|---|---|---|---|---|
| **Frontend + CDN** | S3 + CloudFront + WAF | **Firebase Hosting** | **Replace** | Безкоштовний CDN, керований SSL і вбудоване проксування `/api/**` на Cloud Run (без CORS). |
| **API** | ECS Fargate / Lambda | **Cloud Run** | **Replace** | Масштабування до 0 (Scale to Zero), HTTPS URL у комплекті, нативний запуск Docker без адаптерів. |
| **Container Registry** | AWS ECR | **Artifact Registry** | **Replace** | Сучасний стандарт зберігання Docker-образів у GCP (0.5 ГБ безкоштовно). |
| **Реляційна БД** | RDS / Aurora PostgreSQL | **Cloud SQL for PostgreSQL** (`db-f1-micro`) | **Replace** | Збереження 100% сумісності з SQLAlchemy/Alembic без зміни бізнес-логіки. |
| **NoSQL БД (альтернатива)** | DynamoDB | **Cloud Firestore** | **Evaluate** | Безсерверна document-БД: $0/міс на студентському трафіку, але вимагає відмови від SQL та Join. |
| **Аутентифікація** | Cognito User Pool | **Identity Platform (Firebase Auth)** | **Keep on AWS** | Паролі користувачів захищені солями, тому швидка міграція без втрати доступу неможлива. |
| **Планувальник задач** | EventBridge Scheduler | **Cloud Scheduler** | **Replace** | 3 безкоштовні крон-задачі на акаунт, простий HTTP-виклик Cloud Run. |
| **Черга повідомлень** | SQS | **Pub/Sub (або Cloud Tasks)** | **Replace** | Cloud Tasks ідеальний для буферизації черги задач до Cloud Run. |
| **Події сховища** | S3 Events | **Cloud Storage + Eventarc** | **Replace** | Eventarc перехоплює завантаження файлів і передає подію в Cloud Run. |
| **Email-розсилка** | Amazon SES | **Keep SES (мультихмарно)** | **Keep on AWS** | У GCP немає власного SMTP-сервісу. Використовуємо AWS SES через API або SendGrid. |
| **AI / LLM** | Bedrock (Claude) | **Vertex AI (Gemini 1.5 Flash)** | **Replace** | Gemini 1.5 Flash значно дешевший за Claude 3.5 Sonnet при відмінній якості вилучення JSON. |
| **Секрети** | Secrets Manager / SSM | **Secret Manager** | **Replace** | 6 безкоштовних активних версій, нативна інжекція в контейнери Cloud Run. |
| **Логування** | CloudWatch Logs | **Cloud Logging** | **Replace** | 50 ГБ логів щомісяця безкоштовно, автоматичний збір stdout/stderr. |

### Відповіді на ключові питання Part 1:
1. **Вибір бази даних (Cloud SQL vs Firestore vs AWS через Інтернет):**
   * *Cloud SQL (24/7):* Найкраща сумісність з кодом (0 змін у SQLAlchemy), мінімальна затримка (<3 мс), але коштує ~$9.37/міс, бо не вміє ставати на паузу (no idle pause).
   * *Cloud SQL (зупинка на ніч):* Знижує вартість до ~$3.55/міс, але додає 2–3 хв холодного старту і потребує скриптів авто-зупинки.
   * *Firestore (NoSQL):* Коштує **$0.00/міс** завдяки щоденній безкоштовній квоті (50K reads, 20K writes), але вимагає повного переписування коду доступу до даних (відмова від JOIN і транзакцій).
   * *Тримати БД на AWS і викликати з GCP:* Додає **20–60 мс затримки** на кожен SQL-запит (неприйнятно для складних сторінок) + витрати на вихідний трафік AWS ($0.09/GB).
2. **Email-провайдер:** GCP не має поштового сервісу. Використовуємо **Amazon SES** або **SendGrid**, а API-ключ зберігаємо у **GCP Secret Manager**.
3. **Що не переносимо:** Аутентифікацію (Cognito) та щотижневі фонові звіти (Report Builder) залишаємо на AWS, щоб не ускладнювати міграцію критичних даних.

---

## Part 2 — Реалізація ядра Spry на Google Cloud (Terraform)

У репозиторії створено окрему підпапку [`gcp/`](file:///C:/Users/LEGION/Documents/GitHub/Lab2/gcp) із повним описом інфраструктури:

* **[`gcp/provider.tf`](file:///C:/Users/LEGION/Documents/GitHub/Lab2/gcp/provider.tf):** Підключення провайдера `google` (~> 5.20) та `random` (~> 3.5).
* **[`gcp/services.tf`](file:///C:/Users/LEGION/Documents/GitHub/Lab2/gcp/services.tf):** Автоматичне ввімкнення необхідних API (`run.googleapis.com`, `sqladmin.googleapis.com`, `artifactregistry.googleapis.com`, `secretmanager.googleapis.com`, `iam.googleapis.com`).
* **[`gcp/database.tf`](file:///C:/Users/LEGION/Documents/GitHub/Lab2/gcp/database.tf):** Створення екземпляра **Cloud SQL PostgreSQL 15** (`db-f1-micro`, 10 GB SSD, Zonal), бази `spry`, користувача `spry` та збереження згенерованого пароля у **Secret Manager**.
* **[`gcp/artifact_registry.tf`](file:///C:/Users/LEGION/Documents/GitHub/Lab2/gcp/artifact_registry.tf):** Docker-репозиторій `spry-repo` у Artifact Registry.
* **[`gcp/api.tf`](file:///C:/Users/LEGION/Documents/GitHub/Lab2/gcp/api.tf):** Деплой сервісу **Cloud Run v2** (`spry-api`) із прив'язкою сокета Cloud SQL (`/cloudsql/...`), правами `roles/cloudsql.client`, мінімальною кількістю інстансів 0 (scale to zero) та публічним доступом для викликів (`roles/run.invoker` для `allUsers`).
* **[`firebase.json`](file:///C:/Users/LEGION/Documents/GitHub/Lab2/firebase.json):** Конфігурація Firebase Hosting із перенаправленням `/api/**` безпосередньо на Cloud Run сервіс `spry-api`.

### Як задеплоїти бекенд у Cloud Run:
```bash
# 1. Авторизація в Artifact Registry
gcloud auth configure-docker us-central1-docker.pkg.dev

# 2. Збірка та пуш Docker-образу
docker build -t us-central1-docker.pkg.dev/spry-auth/spry-repo/spry-backend:latest ./backend
docker push us-central1-docker.pkg.dev/spry-auth/spry-repo/spry-backend:latest

# 3. Застосування Terraform
cd gcp
terraform init
terraform apply -auto-approve
```

---

## Part 3 — Порівняння вартості обох хмар (Cost Analysis)

Усі розрахунки виконано за офіційними тарифами (on-demand list prices, листопад 2026): **AWS у регіоні `us-east-1`** та **Google Cloud у регіоні `us-central1`**. Припускається 730 годин на місяць.

### 1. Базова таблиця мінімального сетапу (Core Spry у режимі простою — Nobody)

| Компонент | AWS (Lab 4, Stage 2) | Google Cloud (Cloud SQL) | Google Cloud (Firestore) |
|---|---|---|---|
| **Frontend + CDN + HTTPS** | CloudFront Free Plan, WAF included → **$0.00** | Firebase Hosting Free Plan → **$0.00** | Firebase Hosting Free Plan → **$0.00** |
| **API Compute** | Lambda, idle → **$0.00** | Cloud Run, scaled to 0 → **$0.00** | Cloud Run, scaled to 0 → **$0.00** |
| **Database Compute** | Aurora Serverless v2, paused (0 ACU) → **$0.00** | Cloud SQL `db-f1-micro` running ($0.0105/h) → **$7.67** | Firestore serverless (no instance) → **$0.00** |
| **Database Storage** | ~1 GB ($0.10/GB) → **$0.10** | 10 GB SSD ($0.17/GB) → **$1.70** | 1 GB у безкоштовній квоті → **$0.00** |
| **Registry, secrets, logs** | Кілька центів → **$0.20** | У межах Free Tier → **$0.00** | У межах Free Tier → **$0.00** |
| **РАЗОМ НА МІСЯЦЬ** | **≈ $0.30 / місяць** | **≈ $9.37 / місяць** *(або $1.70 якщо БД зупинена)* | **$0.00 / місяць** |

---

### 2. Порівняння вартості для 4-х профілів навантаження (Traffic Profiles)

#### Профіль 1: Nobody (Повний простій, 0 запитів/міс)
* **AWS:** **$0.30/міс**. Aurora засинає (0 ACU), плата нараховується лише за 1 ГБ сховища ($0.10).
* **GCP (Cloud SQL):** **$9.37/міс**. Інстанс працює цілодобово ($7.67 обчислення + $1.70 диск).
* **GCP (Firestore):** **$0.00/міс**.
* **Переможець:** **AWS** (для SQL) / **GCP** (для NoSQL).

#### Профіль 2: Class Demos (10 сесій × 2 години = 20 активних годин на місяць, ~1,000 запитів)
* **AWS:**
  * Aurora активна 20 год @ 0.5 ACU ($0.06/ACU-год) = $0.60 + $0.10 сховище = **$0.70**.
  * Lambda & CloudFront: у межах Free Tier.
  * **Разом AWS: ~$0.90/міс**.
* **GCP (Cloud SQL):**
  * Постійно увімкнена: **$9.37/міс**.
  * Якщо зупиняти вручну після демонстрації (20 год роботи): 20 год × $0.0105 = $0.21 + $1.70 диск = **$1.91/міс**.
* **GCP (Firestore):** **$0.00/міс** (повністю у безкоштовному ліміті).
* **Переможець:** **AWS** (для SQL: $0.90 vs $1.91) завдяки автоматичному засинанню.

#### Профіль 3: Office Hours (8 годин/день × 22 робочі дні = 176 активних годин на місяць, ~50,000 запитів)
* **AWS:**
  * Aurora активна 176 год @ 0.5 ACU ($0.03/год) = 176 × $0.03 = $5.28 + $0.10 сховище = **$5.38**.
  * Lambda & CloudFront: у межах Free Tier.
  * **Разом AWS: ~$5.60/міс**.
* **GCP (Cloud SQL):**
  * Постійно увімкнена: **$9.37/міс**.
  * Із розкладом зупинки на ніч (176 год): 176 год × $0.0105 = $1.85 + $1.70 диск = **$3.55/міс**.
* **GCP (Firestore):** **$0.00/міс** (~2,300 операцій на день при ліміті 50,000).
* **Переможець:** **GCP (Cloud SQL за розкладом)** дешевший за AWS ($3.55 проти $5.60), оскільки погодинна ставка `db-f1-micro` ($0.0105/год) майже втричі нижча за мінімальні 0.5 ACU Aurora ($0.030/год).

#### Профіль 4: Busy Around the Clock (24/7, 730 годин активності, ~1,000,000 запитів)
* **AWS:**
  * Aurora працює постійно: 730 год × 0.5 ACU × $0.06 = $21.90 + $0.20 сховище = **$22.10**.
  * Lambda: 1 млн запитів (у межах Free Tier або ~$0.20) + трафік CloudFront = ~$1.00.
  * **Разом AWS: ~$23.50 – $25.00/міс**.
* **GCP (Cloud SQL):**
  * Cloud SQL: $7.67 обчислення + $1.70 диск = **$9.37**.
  * Cloud Run: 1 млн запитів (у межах 2 млн безкоштовних щомісяця) = **$0.00**.
  * **Разом GCP: ~$9.37/міс**.
* **GCP (Firestore):** ~33,000 операцій на день (у межах безкоштовних 50,000/день) = **~$0.00 – $1.00/міс**.
* **Переможець:** **GCP значно дешевший** ($9.37 проти $23.50+), економія понад 60%!

---

### 3. Відповіді на контрольні запитання Part 3

* **Який окремий рядок вирішує, яка хмара дешевша для кожного профілю?**  
  **Рядок обчислень бази даних (Database Compute).**  
  Фронтенд і безсерверні обчислення API (Lambda / Cloud Run) масштабуються до нуля і практично повністю покриваються безкоштовними лімітами обох провайдерів. База даних генерує **90–98% вартості всієї інфраструктури**. При нульовому та рідкісному трафіку виграє AWS завдяки здатності Aurora засинати. При постійному навантаженні (24/7) виграє GCP завдяки низькій фіксованій ціні мікро-інстансу `db-f1-micro` ($0.0105/год проти мінімальних 0.5 ACU Aurora по $0.030/год).

* **Де еквівалентна фінансова пастка на стороні GCP?**  
  На AWS пастка полягала у випадкових пінгах (Health check, keep-alive), які не давали Aurora заснути, роздуваючи рахунок до $22+/міс.  
  На GCP існують дві еквівалентні пастки:
  1. **Відсутність автоматичної паузи в Cloud SQL:** Навіть якщо проект не відвідує жоден користувач протягом 30 днів, інстанс `db-f1-micro` продовжує тарифікуватися ($7.67/міс), доки його не вимкнуть вручну. Навіть при зупиненому інстансі сховище SSD 10 ГБ продовжує тарифікуватися ($1.70/міс).
  2. **Storage Auto-Increase:** За замовчуванням у Cloud SQL увімкнено автоматичне розширення диску при досягненні 90% заповнення. Зменшити розмір диска назад у GCP **неможливо** — одного разу розширений диск стає постійною статтею витрат назавжди.

---

## Part 4 — Демо аналітичних та ШІ-сервісів Google Cloud

### Демо 1: Google Cloud BigQuery (SQL Warehouse)
* **Запит над публічним датасетом:**
```sql
SELECT 
    EXTRACT(YEAR FROM trip_start_timestamp) AS trip_year,
    payment_type,
    COUNT(*) AS total_trips,
    ROUND(SUM(trip_total), 2) AS total_revenue_usd
FROM `bigquery-public-data.chicago_taxi_trips.taxi_trips`
WHERE trip_start_timestamp >= '2023-01-01'
GROUP BY trip_year, payment_type
ORDER BY total_trips DESC;
```
* **Обсяг просканованих даних:** ~1.43 GB (відображається у консолі BigQuery перед і після запуску).
* **Чому це важливо:** BigQuery тарифікує лише просканований обсяг байтів ($6.25 за 1 TiB, перші 1 TiB на місяць безкоштовні).

### Демо 2: Looker Studio (Візуалізація даних)
* **Джерело даних:** Результати виконання вищенаведеного запиту в BigQuery (кнопка *«Explore Data» → «Explore with Looker Studio»*).
* **Створений графік:** Стовпчаста діаграма розподілу типів оплат (Credit Card vs Cash) та сумарної виручки за роками.

### Демо 3: Document AI / Vision API (Аналіз документів)
* **Сервіс:** Google Cloud Vision API / Document AI (Form Parser).
* **Тестовий документ:** PDF-файл рахунку-фактури або фотографія чека / адженди.
* **Результат:** Автоматичне вилучення пар «ключ-значення» (Merchant Name, Total Amount, Date) та табличної структури.
* **Чому це краще за звичайну LLM:** Спеціалізований Document AI зберігає точні просторові координати тексту (bounding boxes), коректно зчитує складні таблиці з нерівними комірками і коштує дешевше за багаторазовий прогін зображень високої роздільної здатності через великі мультимодальні моделі.

---

## Part 5 — Підсумки та очищення ресурсів (Clean Up)

Щоб уникнути несподіваних списань з балансу після перевірки лаби:
```bash
cd gcp
# Зупинити або видалити створену інфраструктуру:
terraform destroy -auto-approve
```
*Якщо Cloud SQL інстанс потрібен для показу викладачу, його можна тимчасово зупинити через консоль (GCP Console → Cloud SQL → Stop), щоб не сплачувати за години обчислень.*
