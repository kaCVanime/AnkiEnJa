from src.anki.manager import AnkiManager, results_recorder


results_recorder.start()
m = AnkiManager('KEXP2')

m.run()