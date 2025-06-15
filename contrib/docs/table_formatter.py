text = r"""
Наименование показателя & Значение \\ \hline
Время разработки, ч. & 768 \\ \hline
Основная заработная плата, руб. & 16171.92 \\ \hline
Дополнительная заработная плата, руб. & 2425.79 \\ \hline
Отчисления в Фонд социальной защиты населения, руб. & 6323.22 \\ \hline
Отчисления в БРУСП «Белгосстрах», руб. & 111.59 \\ \hline
Прочие прямые затраты, руб. & 148 \\ \hline
Накладные расходы, руб. & 6885.96 \\ \hline
Полная себестоимость, руб. & 33266.47 \\ \hline
Цена продукта, руб. & 47903.72 \\ \hline
Прибыль от продажи, руб. & 6653.29 \\ \hline
Чистая прибыль, руб. & 5322.64 \\ \hline
"""

with open('table-output.txt', 'w') as file:
    lines = text.split('\n')[1:-1]
    end_lines = []
    for line in lines:
        the_end = r'\\ \hline'
        if not line.endswith(the_end):
            print(f'Line {line} does not end porperly')
            break
        line = line[:-9]
        parts = line.split('&')
        end_lines.append('\t'.join(map(lambda x: x.strip(), parts)))
    file.write('\n'.join(end_lines))
