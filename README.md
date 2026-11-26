# محبان — راهنمای ویرایش صفحات

برای تغییر **رنگ، فونت، اندازه یا فاصله‌ها** از ستون «استایل» شروع کنید. برای تغییر **متن، ترتیب عناصر یا ساختار صفحه**، قالب HTML را ویرایش کنید. بعضی صفحه‌ها CSS جداگانه ندارند و استایلشان داخل تگ `<style>` یا ویژگی `style=` در همان قالب است.

## مسیر استایل هر بخش

| بخش | استایل | قالب HTML |
| --- | --- | --- |
| صفحهٔ اصلی | `home_page/static/home_page/landing.css` | `home_page/templates/home_page/index.html` |
| کارت کمک مالی در صفحهٔ اصلی | `home_page/static/home_page/donation-card.css` | `home_page/templates/home_page/donation_card.html` |
| صفحهٔ کمک مالی | `donations/static/donations/donation.css` | `donations/templates/donations/donation_page.html` |
| اطلاعیه‌ها | `announcements/static/announcements/list.css` برای فهرست؛ `announcements/static/announcements/gallery.css` برای جزئیات | `announcements/templates/announcements/` |
| آرشیو و جزئیات گزارش‌ها | تگ `<style>` داخل قالب همان صفحه | `reports_media/templates/reports_media/archive.html` و `reports_media/templates/reports_media/detail.html` |
| نشریات | استایل عمومی؛ برای تغییر مختص نشریات، CSS را در قالب همان صفحه اضافه کنید | `publications/templates/publications/` |
| تجمعات شبانه | `night_gatherings/static/night_gatherings/gatherings.css`؛ بعضی استایل‌های پخش‌کننده در `player.html` | `night_gatherings/templates/night_gatherings/` |
| پویش‌ها و ثبت‌نام خُدام | `registrations_campaigns/static/registrations_campaigns/forms.css` | `registrations_campaigns/templates/registrations_campaigns/` |
| نظرها و نظرسنجی | استایل عمومی؛ برای تغییر مختص نظرسنجی، CSS را در قالب همان صفحه اضافه کنید | `feedback_polls/templates/feedback_polls/` |
| پخش زنده (صفحهٔ عمومی) | `live/static/live/live.css` | `live/templates/live/live_page.html` |
| فرم مدیریت پخش زنده | `live/static/live/management.css` | `live/templates/live/management.html` |
| ورود و تغییر رمز | استایل عمومی؛ برای تغییر مختص فرم، CSS را در قالب همان صفحه اضافه کنید | `accounts/templates/accounts/` |
| داشبورد حساب کاربری | `site_ui/static/site_ui/account-dashboard.css` و `site_ui/static/site_ui/account-portal.css`؛ این فایل‌ها در قاب مشترک پنل هم بارگذاری می‌شوند | `accounts/templates/accounts/account.html` |
| پنل مدیریت سایت | تگ `<style>` داخل قالب‌های `section.html`، `list.html`، `detail.html`، `form.html` و `delete.html`؛ استایل مشترک در `site_ui/static/site_ui/workspace.css` و `site_ui/templates/site_ui/workspace_base.html` | `workspace/templates/workspace/` |
| تجربه‌نگاری | `site_ui/static/site_ui/workspace.css` (مشترک)؛ برای تغییر مختص تجربه‌نگاری، CSS را در قالب‌های خود اپ اضافه کنید | `experience_writing/templates/experience_writing/` |
| هدر، منو و استایل عمومی | `site_ui/static/site_ui/base.css` | `site_ui/templates/site_ui/base.html` |
| فیلتر واحدها | کلاس‌های `.unit-filter` و `.unit-select` در `site_ui/static/site_ui/base.css`؛ صفحهٔ اصلی استایل اختصاصی خودش را در `landing.css` دارد | `site_ui/templates/site_ui/filter_form.html` و `site_ui/templates/site_ui/unit_select.html` |
| فونت عمومی | `site_ui/static/site_ui/fonts.css` | از قالب پایه بارگذاری می‌شود |
| فوتر عمومی | `site_info/static/site_info/footer.css` | `site_info/templates/site_info/footer.html` |

## تغییر ظاهر فقط یک صفحه

اگر فایل استایل مشترک است و نمی‌خواهید ظاهر صفحه‌های دیگر عوض شود، آن فایل را ویرایش نکنید. در قالب صفحه از بلوک `extra_css` استفاده کنید و سلکتورها را به یک کلاس اختصاصی همان صفحه محدود کنید. اگر قالب از قبل بلوک `extra_css` دارد، تغییر را در همان بلوک بگذارید؛ `{{ block.super }}` استایل‌های به‌ارث‌رسیده را نگه می‌دارد. برای نمونه، اگر کلاس `publication-list` را به عنصر اصلی فهرست نشریات اضافه کرده‌اید:

```django
{% block extra_css %}
  {{ block.super }}
  <style>
    .publication-list h1 { color: #165b49; }
  </style>
{% endblock %}
```

اگر نمی‌دانید کدام فایل رنگ یا فاصلهٔ فعلی را تعیین می‌کند، در مرورگر روی همان عنصر راست‌کلیک کنید، **Inspect** را بزنید و در پنل **Styles** نام فایل و شمارهٔ خط را ببینید. بعد از ذخیره، اگر هنوز استایل قدیمی را می‌بینید، با `Ctrl+F5` صفحه را دوباره بارگذاری کنید.

فایل‌های پوشهٔ `staticfiles/` را دستی تغییر ندهید؛ این پوشه خروجی استقرار است. برای انتشار تغییرات CSS و تصاویر، فایل‌های اصلی را ویرایش کنید و در محیط استقرار `python manage.py collectstatic --noinput` را اجرا کنید.
