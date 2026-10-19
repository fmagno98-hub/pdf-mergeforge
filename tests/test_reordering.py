from pdf_merger_desktop.main_window import move_indices_down, move_indices_up


def test_move_multiple_up() -> None:
    assert move_indices_up(list("ABCDE"), {2, 3}) == (list("ACDBE"), {1, 2})


def test_move_multiple_down() -> None:
    assert move_indices_down(list("ABCDE"), {1, 2}) == (list("ADBCE"), {2, 3})
