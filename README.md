# SEO Content Generator

این پروژه یک سیستم تولید محتوای SEO است که به صورت خودکار محتوای بهینه‌سازی شده برای موتورهای جستجو تولید می‌کند.

## ویژگی‌ها

- تولید خودکار عنوان و توضیحات متا
- بهینه‌سازی محتوا برای SEO
- پشتیبانی از تصاویر و لینک‌ها
- ساختار HTML استاندارد
- سازگار با موبایل
- پشتیبانی از Schema.org markup

## پیش‌نیازها

- Python 3.8+
- SQL Server
- دسترسی به API های مورد نیاز

## نصب

1. مخزن را کلون کنید:
```bash
git clone https://github.com/yourusername/seo-content-generator.git
cd seo-content-generator
```

2. وابستگی‌ها را نصب کنید:
```bash
pip install -r requirements.txt
```

3. فایل تنظیمات را ویرایش کنید:
```bash
cp config.example.py config.py
# فایل config.py را با اطلاعات خود ویرایش کنید
```

## استفاده

1. اتصال به دیتابیس را تنظیم کنید:
```python
SERVER = "your_server"
DATABASE = "your_database"
USERNAME = "your_username"
PASSWORD = "your_password"
```

2. برنامه را اجرا کنید:
```bash
python AiContentGenerator/main.py
```

## ساختار پروژه

```
seo-content-generator/
├── AiContentGenerator/
│   ├── main.py
│   └── content_manager/
│       ├── content_manager.py
│       └── content_database.py
├── requirements.txt
├── config.py
└── README.md
```

## مشارکت

از مشارکت شما استقبال می‌کنیم! لطفاً برای مشارکت:

1. یک issue ایجاد کنید
2. یک branch جدید ایجاد کنید
3. تغییرات خود را commit کنید
4. یک pull request ایجاد کنید

## مجوز

این پروژه تحت مجوز MIT منتشر شده است. برای جزئیات بیشتر به فایل LICENSE مراجعه کنید. 