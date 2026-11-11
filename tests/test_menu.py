"""Small regression checks for the static menu snapshot and generated HTML."""
from html.parser import HTMLParser
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import build  # noqa: E402


class InventoryParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.cards = 0
        self.sections = []
        self.filters = []
        self.lang = None
        self.direction = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'html':
            self.lang, self.direction = attrs.get('lang'), attrs.get('dir')
        if tag == 'article' and attrs.get('class') == 'menu-card':
            self.cards += 1
        if tag == 'section' and attrs.get('class') == 'menu-section':
            self.sections.append(attrs.get('id'))
        if tag == 'a' and 'data-filter' in attrs:
            self.filters.append(attrs['data-filter'])


class MenuTests(unittest.TestCase):
    def setUp(self):
        self.categories = build.read_menu()
        self.items = [item for category in self.categories for item in category['items']]

    def test_snapshot_inventory_and_order(self):
        self.assertEqual(len(self.categories), 25)
        self.assertEqual(len(self.items), 203)
        self.assertEqual(self.categories[0]['title'], 'پیش غذا')
        self.assertEqual(self.categories[-1]['title'], 'بازی ها')
        self.assertEqual(self.items[0]['title'], 'سوپ روز')
        self.assertEqual(self.items[0]['price'], 350000)
        self.assertEqual(len({category['id'] for category in self.categories}), 25)

    def test_prices_descriptions_and_images(self):
        self.assertEqual(build.fa_number(92550), '۹۲٬۵۵۰')
        self.assertEqual(build.fa_number(0), '۰')
        corona = next(item for item in self.items if item['title'] == 'آبجو کرونا')
        self.assertEqual((corona['price'], corona['old_price']), (650000, 850000))
        hookah = next(item for item in self.items if item['title'] == 'شب های ال ماسو')
        self.assertIn('875 ت', hookah['description'])
        self.assertIn('\n', hookah['description'])
        self.assertTrue(all(item['image'] and item['price'] >= 0 for item in self.items))
        self.assertFalse(any('@hookah' in item['description'] for item in self.items))

    def test_local_photos_exist_and_have_a_menu_item(self):
        names = {item['title'] for item in self.items}
        self.assertTrue(set(build.LOCAL_IMAGES).issubset(names))
        for filename in build.LOCAL_IMAGES.values():
            self.assertTrue((ROOT / 'assets/images' / filename).is_file(), filename)

    def test_generated_html_matches_source_and_is_complete(self):
        html_path = ROOT / 'index.html'
        before = html_path.read_text(encoding='utf-8')
        build.main()
        html = html_path.read_text(encoding='utf-8')
        self.assertEqual(before, html, 'Run python3 scripts/build.py after changing source files')
        self.assertNotIn('{{SECTIONS}}', html)
        self.assertNotIn('{{CATEGORY_NAV}}', html)
        parser = InventoryParser()
        parser.feed(html)
        self.assertEqual((parser.lang, parser.direction), ('fa', 'rtl'))
        self.assertEqual(parser.cards, len(self.items))
        self.assertEqual(parser.sections, [category['id'] for category in self.categories])
        self.assertEqual(parser.filters, ['all'] + parser.sections)
        self.assertIn('loading="lazy"', html)
        self.assertIn('data-original="https://elmaso-lounge.com/', html)


if __name__ == '__main__':
    unittest.main()
