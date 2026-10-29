"""Крестики-нолики в консоли против непобедимого компьютера (алгоритм минимакс).

Запуск:  python3 tic_tac_toe.py
"""

LINES = [
    (0, 1, 2), (3, 4, 5), (6, 7, 8),  # строки
    (0, 3, 6), (1, 4, 7), (2, 5, 8),  # столбцы
    (0, 4, 8), (2, 4, 6),             # диагонали
]


def winner(board):
    """Возвращает 'X' или 'O', если кто-то победил, иначе None."""
    for a, b, c in LINES:
        if board[a] != " " and board[a] == board[b] == board[c]:
            return board[a]
    return None


def free_cells(board):
    return [i for i, cell in enumerate(board) if cell == " "]


def minimax(board, player, me):
    """Оценка позиции для `me`: +1 победа, 0 ничья, -1 поражение."""
    w = winner(board)
    if w:
        return (1 if w == me else -1), None
    moves = free_cells(board)
    if not moves:
        return 0, None

    other = "O" if player == "X" else "X"
    best_score = -2 if player == me else 2
    best_move = None
    for move in moves:
        board[move] = player
        score, _ = minimax(board, other, me)
        board[move] = " "
        if (player == me and score > best_score) or (player != me and score < best_score):
            best_score, best_move = score, move
    return best_score, best_move


def show(board):
    rows = []
    for r in range(3):
        cells = [board[r * 3 + c] if board[r * 3 + c] != " " else str(r * 3 + c + 1) for c in range(3)]
        rows.append(" " + " | ".join(cells))
    print("\n" + "\n---+---+---\n".join(rows) + "\n")


def ask_move(board):
    while True:
        raw = input("Ваш ход (1-9): ").strip()
        if raw.isdigit() and 1 <= int(raw) <= 9 and board[int(raw) - 1] == " ":
            return int(raw) - 1
        print("Некорректный ход, попробуйте ещё раз.")


def play():
    print("Крестики-нолики! Вы играете за X, компьютер — за O.")
    first = input("Хотите ходить первым? (д/н): ").strip().lower()
    turn = "X" if first in ("", "д", "да", "y", "yes") else "O"
    board = [" "] * 9

    while not winner(board) and free_cells(board):
        show(board)
        if turn == "X":
            board[ask_move(board)] = "X"
        else:
            _, move = minimax(board, "O", "O")
            board[move] = "O"
            print(f"Компьютер ходит в клетку {move + 1}.")
        turn = "O" if turn == "X" else "X"

    show(board)
    result = winner(board)
    if result == "X":
        print("Вы победили! Невероятно!")
    elif result == "O":
        print("Компьютер победил.")
    else:
        print("Ничья!")


if __name__ == "__main__":
    try:
        while True:
            play()
            if input("Сыграть ещё? (д/н): ").strip().lower() not in ("д", "да", "y", "yes"):
                break
    except (KeyboardInterrupt, EOFError):
        print()
    print("Спасибо за игру!")
