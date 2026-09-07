from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import TestCase, override_settings
from django.urls import reverse

from .views import _read_chores


class ReadChoresTests(TestCase):
    def test_reads_checked_and_unchecked_chores(self):
        with TemporaryDirectory() as temporary_directory:
            chores_path = Path(temporary_directory) / "chores.md"
            chores_path.write_text(
                "# Weekly Chores\n\n"
                "- [ ] Vacuum living room\n"
                "- [x] Clean bathroom sink\n"
                "- [X] Take out recycling\n",
                encoding="utf-8",
            )

            chores = _read_chores(chores_path)

        self.assertEqual(
            chores,
            [
                {"name": "Vacuum living room", "done": False},
                {"name": "Clean bathroom sink", "done": True},
                {"name": "Take out recycling", "done": True},
            ],
        )

    def test_ignores_headers_and_unrecognized_lines(self):
        with TemporaryDirectory() as temporary_directory:
            chores_path = Path(temporary_directory) / "chores.md"
            chores_path.write_text(
                "# Weekly Chores\n"
                "A note, not a chore\n"
                "- Vacuum living room\n"
                "- [ ] Water plants\n",
                encoding="utf-8",
            )

            chores = _read_chores(chores_path)

        self.assertEqual(chores, [{"name": "Water plants", "done": False}])

    def test_missing_file_returns_empty_list(self):
        with TemporaryDirectory() as temporary_directory:
            chores = _read_chores(Path(temporary_directory) / "missing.md")

        self.assertEqual(chores, [])


class ChoreListViewTests(TestCase):
    def test_renders_chores_from_markdown(self):
        with TemporaryDirectory() as temporary_directory:
            chores_path = Path(temporary_directory) / "chores.md"
            chores_path.write_text(
                "- [ ] Vacuum living room\n- [x] Clean bathroom sink\n",
                encoding="utf-8",
            )

            with override_settings(BASE_DIR=Path(temporary_directory)):
                response = self.client.get(reverse("chores:list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Vacuum living room")
        self.assertContains(response, "Clean bathroom sink")
        self.assertContains(response, '<input type="checkbox" disabled>')
        self.assertContains(response, '<input type="checkbox" checked disabled>')

    def test_missing_markdown_shows_empty_state(self):
        with TemporaryDirectory() as temporary_directory:
            with override_settings(BASE_DIR=Path(temporary_directory)):
                response = self.client.get(reverse("chores:list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No chores have been added yet.")
