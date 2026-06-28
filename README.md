# 🏥 Med25 – Клиент-серверное приложение для управления медицинскими данными

Med25 – это веб-приложение для автоматизации работы медицинского учреждения (клиники, поликлиники). Система позволяет вести учёт пациентов, управлять медицинскими картами, расписанием приёма врачей, обмениваться сообщениями между администратором и пациентами, а также управлять документами и медицинским оборудованием.

Проект реализован на **Django** с использованием **Django Templates** (серверный рендеринг), базы данных **PostgreSQL** и развёртывается в контейнерах **Docker**.

Обратный прокси доступен по адресу: <https://github.com/DucZuyVuTM/Med25>

---

## 🛠 Технологический стек

| Компонент            | Технология                                      |
|----------------------|------------------------------------------------ |
| **Backend**          | Python 3.10, Django 5.2, Django ORM             |
| **Frontend**         | Django Templates, HTML5, CSS3, Bootstrap 5      |
| **База данных**      | PostgreSQL (production), SQLite (dev/test)      |
| **Контейнеризация**  | Docker, Docker Compose                          |
| **Веб-сервер**       | Gunicorn (WSGI) + Nginx (reverse proxy/статика) |
| **Тестирование**     | Django TestCase, фаззинг-тесты                  |
| **Развёртывание**    | Render.com (или любой хостинг с Docker)         |

---

## 📁 Структура проекта

```txt
Med25                                                  
├─ accounts  # Управление пользователями и ролями
│  ├─ migrations/
│  ├─ admin.py                                         
│  ├─ apps.py                                          
│  ├─ forms.py                                         
│  ├─ models.py                                        
│  ├─ signals.py                                       
│  ├─ tests.py                                         
│  ├─ urls.py                                          
│  ├─ views.py                                         
│  └─ __init__.py                                      
├─ documents  # Управление документами
│  ├─ migrations/                                   
│  ├─ admin.py                                         
│  ├─ apps.py                                          
│  ├─ models.py                                        
│  ├─ tests.py                                         
│  ├─ urls.py                                          
│  ├─ views.py                                         
│  └─ __init__.py                                      
├─ equipment  # Учёт медицинского оборудования
│  ├─ migrations/
│  ├─ admin.py                                         
│  ├─ apps.py                                          
│  ├─ models.py                                        
│  ├─ tests.py                                         
│  ├─ urls.py                                          
│  ├─ views.py                                         
│  └─ __init__.py                                      
├─ med25  # Основная конфигурация
│  ├─ admin_widgets.py                                 
│  ├─ asgi.py                                          
│  ├─ settings.py                                      
│  ├─ urls.py                                          
│  ├─ wsgi.py                                          
│  └─ __init__.py                                      
├─ messaging  # Обмен сообщениями
│  ├─ migrations/
│  ├─ admin.py                                         
│  ├─ apps.py                                          
│  ├─ models.py                                        
│  ├─ tests.py                                         
│  ├─ urls.py                                          
│  ├─ views.py                                         
│  └─ __init__.py                                      
├─ patients  # Управление пациентами и медкартами
│  ├─ migrations/
│  ├─ admin.py                                         
│  ├─ apps.py                                          
│  ├─ models.py                                        
│  ├─ tests.py                                         
│  ├─ urls.py                                          
│  ├─ views.py                                         
│  └─ __init__.py                                      
├─ scheduling  # Расписание и запись на приём
│  ├─ migrations/
│  ├─ admin.py                                         
│  ├─ apps.py                                          
│  ├─ models.py                                        
│  ├─ tests.py                                         
│  ├─ urls.py                                          
│  ├─ views.py                                         
│  └─ __init__.py                                      
├─ static/
├─ templates  # Шаблоны
│  ├─ accounts                                         
│  │  ├─ edit_profile.html                             
│  │  └─ profile.html                                  
│  ├─ documents                                        
│  │  ├─ create.html                                   
│  │  ├─ detail.html                                   
│  │  └─ list.html                                     
│  ├─ equipment                                        
│  │  └─ list.html                                     
│  ├─ includes                                         
│  │  ├─ footer.html                                   
│  │  ├─ header.html                                   
│  │  └─ paginator.html                                
│  ├─ messaging                                        
│  │  ├─ create.html                                   
│  │  ├─ inbox.html                                    
│  │  └─ thread.html                                   
│  ├─ pages                                            
│  │  ├─ 403csrf.html                                  
│  │  ├─ 404.html                                      
│  │  ├─ 500.html                                      
│  │  └─ home.html                                     
│  ├─ patients                                         
│  │  ├─ card.html                                     
│  │  ├─ detail.html                                   
│  │  └─ list.html                                     
│  ├─ registration                                     
│  │  ├─ logged_out.html                               
│  │  ├─ login.html                                    
│  │  ├─ password_change_done.html                     
│  │  ├─ password_change_form.html                     
│  │  ├─ password_reset_complete.html                  
│  │  ├─ password_reset_confirm.html                   
│  │  ├─ password_reset_done.html                      
│  │  ├─ password_reset_form.html                      
│  │  └─ registration_form.html                        
│  ├─ scheduling                                       
│  │  ├─ detail.html                                   
│  │  └─ list.html                                     
│  └─ base.html                                        
├─ Dockerfile                                          
├─ manage.py                                           
├─ README.md                                           
└─ requirements.txt                                    
```

---

## 💻 Требования к окружению

- Python 3.10 или выше
- Docker и Docker Compose (опционально, для контейнерного запуска)
- PostgreSQL (если запуск без Docker)
- Git

---

## 🚀 Локальный запуск проекта

1. **Клонировать репозиторий**

```bash
git clone https://github.com/DucZuyVuTM/Med25-backend.git
cd Med25
```

2. **Создать виртуальное окружение**

```bash
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows
```

3. **Установить зависимости**

```bash
pip install -r requirements.txt
```

4. **Настроить переменные окружения**

```bash
cp .env.example .env
# Отредактировать .env
```

5. **Выполнить миграции базы данных**

```bash
python manage.py migrate
```

6. **Создать суперпользователя**

```bash
python manage.py createsuperuser
```

7. **Запустить сервер разработки**

```bash
python manage.py runserver
```

Приложение будет доступно по адресу: <http://localhost:8000>

8. **Запуск тестов**

```bash
python manage.py test
```

## 📜 Лицензия

Проект разработан в рамках курсовой работы по дисциплине «Проектирование и разработка клиент-серверных приложений».

Автор: **Ву Дык Зуй**

Группа: ИКБО-10-23

Университет: РТУ МИРЭА, 2026

## 🤝 Контакты

По вопросам, связанным с проектом, можно обращаться:

Email: <duczuyvu12@gmail.com>

GitHub: [DucZuyVuTM](https://github.com/DucZuyVuTM)
