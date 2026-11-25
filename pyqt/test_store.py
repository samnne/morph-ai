import tempfile
import unittest
from pathlib import Path
from store import TaskStore


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / 'nested' / 'tasks.json'
        self.store = TaskStore(self.path)

    def test_round_trip(self):
        task = self.store.add('  Buy groceries 🥕  ')
        task['done'] = True
        self.store.save()
        loaded = TaskStore(self.path)
        loaded.load()
        self.assertEqual(loaded.tasks, self.store.tasks)
        self.assertEqual(task['title'], 'Buy groceries 🥕')
        self.assertFalse(self.path.with_suffix('.tmp').exists())

    def test_missing_file(self):
        self.store.load()
        self.assertEqual(self.store.tasks, [])

    def test_empty_task(self):
        with self.assertRaises(ValueError):
            self.store.add('  ')

    def test_invalid_data_preserved(self):
        self.path.parent.mkdir()
        for text in ['invalid json', '{}', '[{"id":"a","title":"test","done":1}]']:
            self.path.write_text(text)
            with self.assertRaises(ValueError):
                self.store.load()
            self.assertEqual(self.path.read_text(), text)

    def test_unique_ids(self):
        first = self.store.add('Same title')
        second = self.store.add('Same title')
        self.assertNotEqual(first['id'], second['id'])


if __name__ == '__main__':
    unittest.main()
