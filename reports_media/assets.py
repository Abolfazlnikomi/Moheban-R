import re
from html.parser import HTMLParser
from pathlib import PurePosixPath
from urllib.parse import parse_qs, urlencode, urlsplit

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator

FORMATS = {
    '.jpg': ('image', 'image/jpeg', 10),
    '.jpeg': ('image', 'image/jpeg', 10),
    '.png': ('image', 'image/png', 10),
    '.webp': ('image', 'image/webp', 10),
    '.mp4': ('video', 'video/mp4', 150),
    '.webm': ('video', 'video/webm', 150),
    '.mp3': ('audio', 'audio/mpeg', 30),
    '.wav': ('audio', 'audio/wav', 30),
    '.ogg': ('audio', 'audio/ogg', 30),
    '.pdf': ('document', 'application/pdf', 20),
}
UPLOAD_HELP = 'عکس JPG/PNG/WebP: ۱۰، ویدیو MP4/WebM: ۱۵۰، صدا MP3/WAV/OGG: ۳۰ و PDF: ۲۰ مگابایت.'


def extension(name):
    return PurePosixPath(name).suffix.lower()


def format_for(name):
    return FORMATS.get(extension(name), ('download', 'application/octet-stream', 0))


def validate_upload(value):
    suffix = extension(value.name)
    _, _, limit = format_for(value.name)
    if not limit:
        raise ValidationError('فرمت فایل مجاز نیست. %(formats)s', params={'formats': UPLOAD_HELP})
    if not value.size or value.size > limit * 1024 * 1024:
        raise ValidationError('فایل خالی است یا از سقف %(limit)s مگابایت بیشتر است.', params={'limit': limit})
    position = value.tell()
    try:
        header = value.read(64)
    finally:
        value.seek(position)
    signatures = {
        '.jpg': header.startswith(b'\xff\xd8\xff'),
        '.jpeg': header.startswith(b'\xff\xd8\xff'),
        '.png': header.startswith(b'\x89PNG\r\n\x1a\n'),
        '.webp': header[:4] == b'RIFF' and header[8:12] == b'WEBP',
        '.mp4': header[4:8] == b'ftyp',
        '.webm': header.startswith(b'\x1a\x45\xdf\xa3') and b'webm' in header,
        '.mp3': header.startswith(b'ID3') or (len(header) >= 2 and header[0] == 255 and header[1] & 224 == 224),
        '.wav': header[:4] == b'RIFF' and header[8:12] == b'WAVE',
        '.ogg': header.startswith(b'OggS') and any(codec in header for codec in (b'OpusHead', b'vorbis', b'Speex')),
        '.pdf': header.startswith(b'%PDF-'),
    }
    if not signatures[suffix]:
        raise ValidationError('ساختار فایل با پسوند آن سازگار نیست.')


def validate_cover(value):
    if format_for(value.name)[0] != 'image':
        raise ValidationError('تصویر شاخص باید JPG، PNG یا WebP باشد.')
    validate_upload(value)


class FrameSource(HTMLParser):
    def __init__(self):
        super().__init__()
        self.sources = []

    def handle_starttag(self, tag, attrs):
        if tag == 'iframe':
            self.sources.append(dict(attrs).get('src') or '')


def checked_url(value):
    if not value or re.search(r'[\s\\\x00-\x1f\x7f]', value):
        raise ValidationError('یک نشانی HTTPS معتبر وارد کنید.')
    URLValidator(schemes=['https'])(value)
    parsed = urlsplit(value)
    if parsed.username or parsed.password or parsed.port not in (None, 443):
        raise ValidationError('نشانی نباید اطلاعات ورود یا پورت غیر استاندارد داشته باشد.')
    return parsed


def resolve_embed(value):
    value = value.strip()
    is_frame = value.startswith('<')
    if is_frame:
        parser = FrameSource()
        try:
            parser.feed(value)
        except (ValueError, AssertionError) as error:
            raise ValidationError('کد iframe معتبر نیست.') from error
        if len(parser.sources) != 1:
            raise ValidationError('کد باید دقیقاً یک iframe با نشانی معتبر داشته باشد.')
        value = parser.sources[0]
        if value.startswith('//'):
            value = 'https:' + value
    parsed = checked_url(value)
    host = parsed.hostname
    path = parsed.path.rstrip('/')
    query = parse_qs(parsed.query)
    if host in {'youtube.com', 'www.youtube.com', 'm.youtube.com', 'youtu.be', 'www.youtube-nocookie.com'}:
        if host == 'youtu.be':
            video = path.lstrip('/')
        elif path == '/watch':
            video = query.get('v', [''])[0]
        else:
            match = re.fullmatch(r'/(?:embed|shorts|live)/([^/]+)', path)
            video = match[1] if match else ''
        if re.fullmatch(r'[A-Za-z0-9_-]{11}', video):
            return 'frame', f'https://www.youtube-nocookie.com/embed/{video}'
    elif host in {'aparat.com', 'www.aparat.com'}:
        match = re.fullmatch(r'/(?:v/|video/video/embed/videohash/)([A-Za-z0-9]+)(?:/vt/frame)?', path)
        if match:
            return 'frame', f'https://www.aparat.com/video/video/embed/videohash/{match[1]}/vt/frame'
    elif host in {'soundcloud.com', 'www.soundcloud.com', 'w.soundcloud.com'}:
        track = query.get('url', [''])[0] if host == 'w.soundcloud.com' else value
        if track:
            target = checked_url(track)
            track_path = target.path.rstrip('/')
            if (
                target.hostname in {'soundcloud.com', 'www.soundcloud.com'}
                and re.fullmatch(r'/[\w-]+/(?:sets/)?[\w-]+', track_path, re.ASCII)
            ) or (
                target.hostname == 'api.soundcloud.com'
                and re.fullmatch(r'/(?:tracks|playlists)/\d+', track_path)
            ):
                canonical = f'https://{target.hostname}{track_path}'
                return 'frame', 'https://w.soundcloud.com/player/?' + urlencode({'url': canonical})
    elif host == 'drive.google.com':
        match = re.fullmatch(r'/file/d/([\w-]+)(?:/(?:view|preview|edit))?', path, re.ASCII)
        document = match[1] if match else query.get('id', [''])[0] if path in {'/open', '/uc'} else ''
        if re.fullmatch(r'[A-Za-z0-9_-]+', document):
            resource_key = query.get('resourcekey', [''])[0]
            suffix = '?' + urlencode({'resourcekey': resource_key}) if resource_key else ''
            return 'document_frame', f'https://drive.google.com/file/d/{document}/preview{suffix}'
    if is_frame:
        raise ValidationError('iframe فقط برای آپارات، یوتیوب، SoundCloud و گوگل درایو پذیرفته می‌شود.')
    kind = format_for(path)[0]
    return (kind if kind != 'download' else 'link'), value


def validate_embed(value):
    resolve_embed(value)
