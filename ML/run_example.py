from ml.service import analyze_project


def main() -> None:
    document_text = """
    Введение
    Цель работы — изучить алгоритмы сортировки.

    Практическая часть
    В ходе работы были рассмотрены примеры сортировки массива.
    """

    result = analyze_project(
        document_text=document_text,
        image_paths=[],
        topic="Алгоритмы сортировки",
    )

    print(result)


if __name__ == "__main__":
    main()
