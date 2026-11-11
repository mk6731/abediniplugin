#!/usr/bin/env python3
"""Build the standalone HTML menu from the editable UTF-8 menu snapshot."""
from html import escape
from pathlib import Path
import re
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
SOURCE = 'https://elmaso-lounge.com/wp-content/uploads/'

# These are local copies of the very same photographs on the original menu.
# Other images load directly from the original website, with lazy loading.
LOCAL_IMAGES = {
    'سوپ روز': 'soup.jpg', 'نان سیر': 'garlic-bread.jpg', 'بوفالو وینگز': 'wings.jpg',
    'سیب زمینی اسپیشیال': 'fries-special.jpg', 'سیب مخصوص ال ماسو': 'fries-elmaso.png',
    'سیب زمینی با سس قارچ': 'fries-mushroom.jpg', 'سیب زمینی با ادویه': 'fries-spiced.jpg',
    'قارچ سوخاری': 'fried-mushrooms.jpg', 'پیاز سوخاری': 'onion-rings.jpg',
    'سالاد مخصوص ال ماسو': 'salad.jpg', 'سالاد سزار سوخاری 4 رول': 'caesar4.jpg',
    'سالاد سزار سوخاری 2 رول': 'caesar2.jpg', 'سالاد سزار گریل': 'caesargrill.jpg',
    'سالاد سزار میکس': 'caesarmix.jpg', 'سالاد آنتراکت': 'entreact.jpg',
    'پاستا مخصوص ال ماسو': 'pasta.jpg', 'پاستا چیکن پارمسان': 'parmesan.jpg', 'پاستا پانا': 'panna.jpg',
    'برگر مخصوص ال ماسو': 'burger.jpg', 'برگر فرانسوی': 'frenchburger.jpg',
    'کریسپی برگ': 'crispyburger.jpg', 'چیزبرگر': 'cheeseburger.jpg',
    'ساندویچ فرایز چیکن': 'panini.jpg', 'بشقاب سوخاری 2 نفره': 'friedchicken.jpg',
    'چیکن استریپس 5 تکه': 'strips5.jpg', 'چیکن استریپس 3 تکه': 'strips3.jpg', 'پاچینی': 'pachini.jpg',
    'پیتزا مخصوص ال ماسو': 'pizza-special.jpg', 'پیتزا پپرونی': 'pepperonipizza.jpg',
    'چلو جوجه زعفرانی مخصوص': 'iranian.jpg', 'چلو لقمه مخصوص': 'rice.jpg', 'استیک مرغ': 'steak.jpg',
    'نوشابه کوکاکولا': 'soda.jpg', 'پیناکولادا': 'pina.jpg', 'موهیتو': 'smoothie.jpg',
    'شیک پینات': 'shake.jpg', 'رد موهیتو': 'mocktail.jpg', 'لیموناد کوبایی': 'lemonade.jpg',
    'کن پانا': 'hotcoffee.jpg', 'کافه لاته': 'latte.jpg', 'اسپرسو سینگل': 'espresso.jpg',
    'قهوه فرانسه': 'brewed.jpg', 'چای سیاه': 'tea.jpg', 'وافل مخصوص': 'cake.jpg',
    'شب های ال ماسو': 'hookah-nights.jpg',
}

HOOKAH = (
    '2 عدد چایی با شارژ رایگان\n'
    'تعویض سری قلیان : 550 ت\n'
    '%30 تخفیف ویژه ( {discount} ت) از 12 الی 17 برای فیش هایی که قبل از 17 تسویه کنند'
)
HOOKAH_NOTE = '''<details class="section-note"><summary>مزایای قلیونای ال ماسو لانژ</summary>
<ul><li>ما فقط از تنباکوی برند و اورجینال استفاده میکنیم ( می تونید سر زده بیاید داخل قلیانکده و ببینید )</li>
<li>هر طعمی یک برندی خوبه به صورت کلی برند های ما الفاخر – نخل – آدالیا – بنگ بنگ – مزایا و همه اورجینال هستند.</li>
<li>ما برای قلیان های عربی و طعم های اصیل ذغال چهار تراش و سکه لیمو شیرین جهرم استفاده می کنیم که برخلاف تصور مردم چند برابر قیمت ذغال های مکعبی یا همون نارگیل هست.</li>
<li>اگه بخواید میتونید درخواست بدید سری عربی رو به شکل گنبدی براتون میزنیم.</li>
<li>بنا به هر دلیلی از قلیونتون خوشتون نیومد یا مشکلی داشت حتما به مدیریت اطلاع بدید ما بشدت روی قلیونامون تعصب داریم</li></ul></details>'''


def fa_number(number):
    return f'{number:,}'.translate(str.maketrans('0123456789,', '۰۱۲۳۴۵۶۷۸۹٬'))


def read_menu():
    categories = []
    ids = set()
    for lineno, line in enumerate((ROOT / 'src/menu.txt').read_text(encoding='utf-8').splitlines(), 1):
        if not line or line.startswith('#'):
            continue
        parts = line.split('|')
        if line.startswith('@'):
            if len(parts) != 3 or parts[0][1:] in ids:
                raise ValueError(f'Invalid or duplicate category on line {lineno}')
            category = {'id': parts[0][1:], 'title': parts[1], 'en': parts[2], 'items': []}
            ids.add(category['id'])
            categories.append(category)
        else:
            if len(parts) != 4 or not categories:
                raise ValueError(f'Invalid item on line {lineno}')
            title, price, image, description = parts
            price_parts = price.split('~')
            if len(price_parts) > 2 or not all(value.isdigit() for value in price_parts):
                raise ValueError(f'Invalid price on line {lineno}')
            if not title or not image:
                raise ValueError(f'Missing title or image on line {lineno}')
            if description.startswith('@hookah'):
                discount = description.removeprefix('@hookah')
                if discount not in {'595', '875'}:
                    raise ValueError(f'Invalid hookah description on line {lineno}')
                description = HOOKAH.format(discount=discount)
            description = description.replace('\\n', '\n')
            # Keep the source wording while giving ingredient separators room to breathe.
            description = re.sub(r'[ \t]*\+[ \t]*', ' + ', description)
            categories[-1]['items'].append({
                'title': title, 'price': int(price_parts[0]),
                'old_price': int(price_parts[1]) if len(price_parts) == 2 else None,
                'image': image, 'description': description,
            })
    if not categories or any(not c['items'] for c in categories):
        raise ValueError('Every category must contain at least one item')
    return categories


def card(item, category, eager=False):
    title = escape(item['title'])
    original = SOURCE + quote(item['image'], safe='/')
    local = LOCAL_IMAGES.get(item['title'])
    if local:
        if not (ROOT / 'assets/images' / local).is_file():
            raise FileNotFoundError(f'Missing local photograph: {local}')
        src = 'assets/images/' + local
        fallback = f' data-original="{escape(original, quote=True)}"'
    else:
        src, fallback = original, ''
    old_price = (f'<span class="old-price">{fa_number(item["old_price"])}</span>'
                 if item['old_price'] is not None else '')
    description = escape(item['description'])
    return f'''<article class="menu-card">
  <div class="card-image"><div class="image-fallback" aria-hidden="true">el maso<small>LOUNGE MENU</small></div>
    <img src="{escape(src, quote=True)}"{fallback} alt="{title}" width="250" height="250" loading="{'eager' if eager else 'lazy'}" decoding="async">
    <span class="card-chip">{escape(category['title'])}</span>
  </div>
  <div class="card-body"><h4 class="card-title">{title}</h4><p class="card-description">{description}</p>
    <div class="card-bottom"><div class="price-wrap">{old_price}<span class="price">{fa_number(item['price'])}</span><span class="currency">تومان</span></div>
      <button class="card-more" type="button" aria-label="مشاهده جزئیات {title}"><span class="card-more-label">جزئیات</span><span class="card-more-icon"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><path d="M18 12H5m6-6-6 6 6 6"/></svg></span></button>
    </div>
  </div>
</article>'''


def main():
    categories = read_menu()
    nav = []
    sections = []
    for number, category in enumerate(categories, 1):
        title, category_id = escape(category['title']), escape(category['id'], quote=True)
        nav.append(f'<a class="category-link" href="#{category_id}" data-filter="{category_id}">{title}</a>')
        cards = '\n'.join(card(item, category, eager=(number == 1 and index < 4))
                          for index, item in enumerate(category['items']))
        note = HOOKAH_NOTE if category['id'] == 'ghel' else ''
        sections.append(f'''<section class="menu-section" id="{category_id}" data-title="{title}" aria-labelledby="heading-{category_id}">
  <div class="section-heading"><div class="section-title-wrap"><span class="section-number" aria-hidden="true">{number:02d}</span><div><h3 id="heading-{category_id}">{title}</h3><span class="section-en">{escape(category['en'])}</span></div></div><span class="section-count">{fa_number(len(category['items']))} آیتم</span></div>
  {note}<div class="card-grid">{cards}</div>
</section>''')
    output = (ROOT / 'src/template.html').read_text(encoding='utf-8')
    replacements = {
        '{{CATEGORY_NAV}}': '\n            '.join(nav),
        '{{SECTIONS}}': '\n          '.join(sections),
        '{{CATEGORY_COUNT}}': fa_number(len(categories)),
        '{{ITEM_COUNT}}': fa_number(sum(len(category['items']) for category in categories)),
    }
    for placeholder, value in replacements.items():
        if output.count(placeholder) != 1:
            raise ValueError(f'Expected exactly one {placeholder} placeholder')
        output = output.replace(placeholder, value)
    (ROOT / 'index.html').write_text(output, encoding='utf-8')
    print(f'Built index.html: {len(categories)} categories, {sum(len(c["items"]) for c in categories)} items')


if __name__ == '__main__':
    main()
