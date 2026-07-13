"""Unit tests for shared helpers in the Shiny test-suite conftest module."""

from __future__ import annotations

import socket

from pathlib import Path

import pytest


@pytest.mark.unit()
class Test_Shiny_Conftest_Helpers:
    """Verify the pure helper functions used by the Shiny server fixture."""

    @pytest.mark.unit()
    def Test_Find_Free_Local_Port_Returns_Usable_Port(self) -> None:
        """The free-port helper should return a valid localhost TCP port."""
        from tests.tests_shiny.conftest import _SHINY_TEST_HOST, _find_free_local_port

        port_server = _find_free_local_port()

        assert isinstance(port_server, int)
        assert 0 < port_server < 65536
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as socket_server:
            socket_server.bind((_SHINY_TEST_HOST, port_server))

    @pytest.mark.unit()
    def Test_Read_Text_File_Tail_Returns_Empty_String_For_Missing_File(
        self,
        tmp_path: Path,
    ) -> None:
        """Missing files should yield an empty tail string."""
        from tests.tests_shiny.conftest import _read_text_file_tail

        result_tail = _read_text_file_tail(tmp_path / "missing.log")

        assert result_tail == ""

    @pytest.mark.unit()
    def Test_Read_Text_File_Tail_Returns_Last_Lines(
        self,
        tmp_path: Path,
    ) -> None:
        """The tail helper should keep only the last requested lines."""
        from tests.tests_shiny.conftest import _read_text_file_tail

        path_log = tmp_path / "server.log"
        path_log.write_text("line1\nline2\nline3\nline4\n", encoding="utf-8")

        result_tail = _read_text_file_tail(path_log, num_lines=2)

        assert result_tail == "line3\nline4"


@pytest.mark.integration()
class Test_Shiny_Conftest_Server_Fixture:
    """Verify the Shiny server fixture returns a localhost URL when startup succeeds."""

    @pytest.mark.integration()
    def Test_Shiny_Server_Url_Fixture_Returns_Localhost_Url(
        self,
        shiny_server_url: str,
    ) -> None:
        """The server fixture should yield an HTTP localhost URL."""
        assert shiny_server_url.startswith("http://127.0.0.1:")