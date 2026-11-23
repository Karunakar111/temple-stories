"""Run the mock demonstrations as a test: python3 -m unittest tests.test_gudi"""
import unittest


class MockScenarios(unittest.TestCase):
    def test_all_scenarios(self):
        from gudi.demo import main

        self.assertEqual(main(), 0)


class ShotListsAndMedia(unittest.TestCase):
    def test_shot_lists_build_and_validate(self):
        import subprocess, sys
        r = subprocess.run([sys.executable, "scripts/plan/shotlists.py"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_payloads_resolve_to_media_ids(self):
        import io, json, contextlib
        from gudi.payload_test import main as pt
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            pt()
        d = json.loads(buf.getvalue())
        still, clip, ext = d["payloads"]
        self.assertEqual(still["held"], [])
        self.assertEqual([m["role"] for m in still["params"]["medias"]], ["image_references", "image_references"])
        self.assertEqual(clip["params"]["medias"][0]["role"], "start_image")
        self.assertTrue(ext["held"])  # identified exterior without a photo is held


# The full seven-film rehearsal with renders takes ~25 min: python3 -m gudi.batch_demo


if __name__ == "__main__":
    unittest.main()
