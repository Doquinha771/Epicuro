from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_windowed_exe_build_has_no_console():
    spec = (ROOT / "Epicuro.spec").read_text(encoding="utf-8")
    assert "console=False" in spec
    assert 'name="Epicuro"' in spec


def test_background_jobs_do_not_keep_process_alive():
    ui = (ROOT / "epicuro" / "ui.py").read_text(encoding="utf-8")
    assert "daemon=True" in ui
    assert "QThread" not in ui
    close_block = ui[ui.index("def closeEvent"):]
    assert "QMessageBox.question" not in close_block
    assert "app.quit()" in close_block


def test_theme_and_local_icons_are_present():
    ui = (ROOT / "epicuro" / "ui.py").read_text(encoding="utf-8")
    icons = (ROOT / "epicuro" / "icons.py").read_text(encoding="utf-8")
    assert "#0B0F14" in ui
    assert "#5B9CFF" in ui
    assert "make_icon" in ui
    assert "QPainter" in icons
    assert 'name == "clipboard"' in icons
    assert 'name == "diagnostic"' in icons
    assert 'name == "cleanup"' in icons


def test_product_name_has_no_dark_suffix():
    core = (ROOT / "epicuro" / "core.py").read_text(encoding="utf-8")
    main = (ROOT / "main.py").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert 'APP_NAME = "Epicuro"' in core
    assert 'setApplicationDisplayName("Epicuro")' in main
    assert "# Epicuro\n" in readme
    assert "Epicuro 3.3 Dark" not in core + main + readme
    assert "Dark Transfer Manager" not in core + main + readme


def test_frozen_spotify_worker_is_supported():
    main = (ROOT / "main.py").read_text(encoding="utf-8")
    core = (ROOT / "epicuro" / "core.py").read_text(encoding="utf-8")
    assert "--spotdl-worker" in main
    assert "console_entry_point" in main
    assert 'getattr(sys, "frozen", False)' in core


def test_spotdl_process_is_console_free_and_pipe_independent():
    core = (ROOT / "epicuro" / "core.py").read_text(encoding="utf-8")
    assert "stdin=subprocess.DEVNULL" in core
    assert "stdout=subprocess.DEVNULL" in core
    assert "stderr=subprocess.DEVNULL" in core
    assert "CREATE_NO_WINDOW" in core
    assert "self._spotify_process.poll()" in core


def test_transfer_table_has_matching_column_count():
    ui = (ROOT / "epicuro" / "ui.py").read_text(encoding="utf-8")
    assert "QTableWidget(0, 9)" in ui
    expected = [
        '"Nome do arquivo"', '"Tamanho"', '"Concluído"', '"Velocidade"',
        '"Progresso"', '"Origem"', '"Formato"', '"Status"', '"Restante"'
    ]
    start = ui.index("self.transfers.setHorizontalHeaderLabels")
    block = ui[start:start + 450]
    for label in expected:
        assert label in block
    assert block.count('"Status"') == 1


def test_library_keeps_paths_in_data_not_a_visible_column():
    ui = (ROOT / "epicuro" / "ui.py").read_text(encoding="utf-8")
    assert "DraggableFileTable(0, 6)" in ui
    assert "FILE_LIST_ROLE" in ui
    start = ui.index("self.completed.setHorizontalHeaderLabels")
    block = ui[start:start + 260]
    assert '"Arquivo"' not in block


def test_build_prefers_reliability_and_venv_pyinstaller():
    spec = (ROOT / "Epicuro.spec").read_text(encoding="utf-8")
    bat = (ROOT / "GERAR_EXE.bat").read_text(encoding="utf-8")
    assert "upx=False" in spec
    assert "python -m PyInstaller" in bat


def test_library_supports_native_file_drag_and_multi_select():
    ui = (ROOT / "epicuro" / "ui.py").read_text(encoding="utf-8")
    assert "class DraggableFileTable" in ui
    assert "QMimeData" in ui
    assert "QUrl.fromLocalFile" in ui
    assert "mime.setUrls" in ui
    assert "QDrag(self)" in ui
    assert "QAbstractItemView.DragOnly" in ui
    assert "QAbstractItemView.ExtendedSelection" in ui
    assert "FILE_LIST_ROLE" in ui


def test_library_has_practical_actions_and_search():
    ui = (ROOT / "epicuro" / "ui.py").read_text(encoding="utf-8")
    for text in ("Abrir arquivo", "Mostrar na pasta", "Copiar caminho", "Remover da biblioteca", "Pesquisar biblioteca"):
        assert text in ui
    assert "apply_library_filter" in ui
    assert "open_file" in ui


def test_tools_area_is_functional_not_an_info_popup():
    ui = (ROOT / "epicuro" / "ui.py").read_text(encoding="utf-8")
    core = (ROOT / "epicuro" / "core.py").read_text(encoding="utf-8")
    assert "class ToolsDialog" in ui
    for text in ("Verificar componentes", "Copiar diagnóstico", "Limpar downloads incompletos", "Recarregar biblioteca"):
        assert text in ui
    assert "runtime_diagnostics" in core
    assert "cleanup_partial_downloads" in core
    assert "find_partial_downloads" in core


def test_git_repository_files_are_ready():
    for name in (".gitignore", ".gitattributes", "LICENSE", "README.md", "requirements-dev.txt"):
        assert (ROOT / name).exists(), name
    license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    assert "MIT License" in license_text
    assert "Permission is hereby granted, free of charge" in license_text
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    for ignored in (".venv/", "build/", "dist/", "data/", "downloads/"):
        assert ignored in gitignore
    assert (ROOT / ".github" / "workflows" / "tests.yml").exists()
