from itertools import chain
from tempfile import TemporaryFile

from django.http import FileResponse
from django.utils import timezone
from openpyxl import Workbook
from openpyxl.cell import WriteOnlyCell
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE


def excel_response(filename, headers, rows):
    workbook = Workbook(write_only=True)
    sheet = workbook.create_sheet('ثبت‌نام‌ها')
    sheet.sheet_view.rightToLeft = True
    for row in chain((headers,), rows):
        cells = []
        for value in row:
            if isinstance(value, str):
                cell = WriteOnlyCell(sheet, value=ILLEGAL_CHARACTERS_RE.sub('', value))
                cell.data_type = 's'
                cells.append(cell)
            else:
                cells.append(value)
        sheet.append(cells)
    stream = TemporaryFile()
    try:
        workbook.save(stream)
        stream.seek(0)
    except Exception:
        stream.close()
        raise
    response = FileResponse(stream, as_attachment=True, filename=filename,
                            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Cache-Control'] = 'private, no-store'
    return response


def volunteer_export(queryset):
    return excel_response(
        'volunteer-applications.xlsx',
        ('نام', 'نام خانوادگی', 'شماره تماس', 'کد ملی', 'تاریخ تولد', 'مهارت‌ها', 'بخش', 'شیفت‌ها', 'وضعیت', 'زمان ثبت'),
        (
            (app.first_name, app.last_name, app.phone, app.national_id, app.birth_date, app.skills,
             app.section.name, app.availability, app.get_status_display(), timezone.localtime(app.created_at).isoformat())
            for app in queryset.select_related('section').iterator()
        ),
    )


def campaign_export(campaign):
    entries = list(campaign.entries.all())
    columns = dict.fromkeys((field.pk, field.label) for field in campaign.fields.all())
    for entry in entries:
        columns.update(dict.fromkeys((answer['id'], answer['label']) for answer in entry.answers))

    def rows():
        for entry in entries:
            answers = {(answer['id'], answer['label']): answer['value'] for answer in entry.answers}
            yield (entry.full_name, entry.phone, timezone.localtime(entry.created_at).isoformat(),
                   *(answers.get(key, '') for key in columns))

    return excel_response(
        f'campaign-{campaign.pk}.xlsx',
        ('نام و نام خانوادگی', 'شماره تماس', 'زمان ثبت', *(label for _, label in columns)),
        rows(),
    )
