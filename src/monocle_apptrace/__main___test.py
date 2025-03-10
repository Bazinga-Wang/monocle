import pytest
import sys
from unittest.mock import patch, MagicMock
from monocle_apptrace.__main__ import main

def test_main_no_args(capsys):
    with patch.object(sys, 'argv', ['monocle_apptrace']):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "Usage: python -m monocle_apptrace <your-main-module-file> <args>" in captured.out

def test_main_invalid_file(capsys):
    with patch.object(sys, 'argv', ['monocle_apptrace', 'test.txt']):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "Usage: python -m monocle_apptrace <your-main-module-file> <args>" in captured.out

def test_main_valid_file():
    mock_runpy = MagicMock()
    mock_setup = MagicMock()

    with patch('monocle_apptrace.__main__.runpy', mock_runpy), \
         patch('monocle_apptrace.__main__.setup_monocle_telemetry', mock_setup), \
         patch.object(sys, 'argv', ['monocle_apptrace', 'test.py', 'arg1']):

        main()

        mock_setup.assert_called_once_with(workflow_name='test')
        mock_runpy.run_path.assert_called_once_with(path_name='test.py', run_name='__main__')

def test_main_run_exception(capsys):
    mock_runpy = MagicMock()
    mock_runpy.run_path.side_effect = Exception("Test error")
    mock_setup = MagicMock()

    with patch('monocle_apptrace.__main__.runpy', mock_runpy), \
         patch('monocle_apptrace.__main__.setup_monocle_telemetry', mock_setup), \
         patch.object(sys, 'argv', ['monocle_apptrace', 'test.py']):

        main()

        captured = capsys.readouterr()
        assert "Test error" in captured.out

def test_main_with_multiple_args():
    mock_runpy = MagicMock()
    mock_setup = MagicMock()

    with patch('monocle_apptrace.__main__.runpy', mock_runpy), \
         patch('monocle_apptrace.__main__.setup_monocle_telemetry', mock_setup), \
         patch.object(sys, 'argv', ['monocle_apptrace', 'test.py', 'arg1', 'arg2']):

        main()

        mock_setup.assert_called_once_with(workflow_name='test')
        mock_runpy.run_path.assert_called_once_with(path_name='test.py', run_name='__main__')
        assert sys.argv == ['test.py', 'arg1', 'arg2']
