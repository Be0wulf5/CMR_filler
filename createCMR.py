import tkinter as tk
from tkinter import ttk
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from pdfrw import PdfReader, PdfWriter, PageMerge
import io
import json
import os

DATA_FILE = "cmr_data.json"
STAMP_FILE = "stamp.png"  # Имя файла штампа


def split_text(text, max_length):
    """Разбивает текст на строки с максимальной длиной max_length"""
    words = text.split()
    lines, current_line = [], ""

    for word in words:
        if len(current_line) + len(word) + 1 > max_length:
            lines.append(current_line)
            current_line = word
        else:
            current_line = current_line + " " + word if current_line else word

    if current_line:
        lines.append(current_line)

    return "\n".join(lines)


def draw_multiline_text(can, text, x, y, line_height):
    """Отрисовка многострочного текста на PDF"""
    for i, line in enumerate(text.split('\n')):
        can.drawString(x, y - i * line_height, line)


def create_cmr_from_template(template_file, output_file, data):
    """Создание CMR накладной на основе шаблона"""
    template_pdf = PdfReader(template_file)
    text_filled_pdfs = []

    text_fields = [
        ("sender", 30, 60, 742),
        ("receiver", 30, 60, 675),
        ("carrier", 20, 65, 105),
        ("place_of_loading", 30, 60, 535),
        ("place_of_unloading", 30, 60, 595),
        ("goods", 40, 60, 430),
        ("goods_2", 40, 60, 400),  # Новое поле "Товары 2"
        ("weight", 30, 435, 430),
        ("pieces", 30, 100, 137),
        ("date_of_dispatch", 30, 210, 137),
        ("vehicle_number", 30, 370, 640)
    ]

    stamp_present = os.path.exists(STAMP_FILE)  # Проверяем наличие штампа

    for template_page in template_pdf.pages:
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=A4)
        can.setFont("Helvetica", 12)

        for field, max_len, x, y in text_fields:
            draw_multiline_text(can, split_text(data[field], max_len), x, y, 15)

        # Если штамп присутствует, добавляем его на PDF
        if stamp_present:
            img = ImageReader(STAMP_FILE)
            can.drawImage(img, 430, 650, width=120, height=48, mask='auto')
            can.drawImage(img, 240, 75, width=120, height=48, mask='auto')

        can.showPage()
        can.save()

        packet.seek(0)
        text_filled_pdfs.append(PdfReader(packet).pages[0])

    for i, page in enumerate(template_pdf.pages):
        PageMerge(page).add(text_filled_pdfs[i]).render()

    PdfWriter(output_file, trailer=template_pdf).write()

    return stamp_present  # Возвращаем статус наличия штампа


def save_data(data):
    """Сохранение введенных данных в файл"""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def load_data():
    """Загрузка данных из файла"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def generate_cmr():
    """Генерация CMR накладной и сохранение введенных данных"""
    data = {entry_key: entries[entry_key].get() for entry_key in entries}
    save_data(data)

    output_file = f"cmr_filled_{data['date_of_dispatch']}.pdf"

    # Создаем ЦМР и получаем статус наличия штампа
    stamp_present = create_cmr_from_template("DokumentCMR.pdf", output_file, data)

    # Настройка жирного красного текста
    status_label.config(foreground="red", font=("Helvetica", 12, "bold"))

    # Выводим разные сообщения в зависимости от наличия файла штампа
    if stamp_present:
        status_label.config(text="CMR накладная создана успешно (штамп добавлен)!")
    else:
        status_label.config(text="CMR накладная создана (без штампа, файл не найден).")

    root.after(1500, root.destroy)


def populate_fields(data):
    """Заполнение полей формы данными"""
    for field, default_value in default_values.items():
        entries[field].insert(0, data.get(field, default_value))


# Создание главного окна
root = tk.Tk()
root.title("CMR Generator")

# Определение полей ввода
fields = [
    ("Отправитель", "sender"),
    ("Получатель", "receiver"),
    ("Штамп отправителя", "carrier"),
    ("Место погрузки", "place_of_loading"),
    ("Место выгрузки", "place_of_unloading"),
    ("Товары", "goods"),
    ("Товары 2", "goods_2"),  # Новое поле "Товары 2"
    ("Вес", "weight"),
    ("Город отправитель", "pieces"),
    ("Дата отправки", "date_of_dispatch"),
    ("Номер транспортного средства", "vehicle_number"),
]

entries = {}
default_values = {
    "sender": "Sender", "receiver": "Receiver", "carrier": "Sender stamp",
    "place_of_loading": "Loading place", "place_of_unloading": "Unloading place",
    "goods": "Goods", "goods_2": "Goods 2",  # Значение по умолчанию для "Товары 2"
    "weight": "Weight", "pieces": "City-sender",
    "date_of_dispatch": "dd-mm-yyyy", "vehicle_number": "Truck / Trailer"
}

# Создание и размещение меток и полей ввода с помощью цикла
for i, (label, entry_key) in enumerate(fields):
    ttk.Label(root, text=label).grid(row=i, column=0, padx=10, pady=5)
    entries[entry_key] = ttk.Entry(root, width=50)
    entries[entry_key].grid(row=i, column=1, padx=10, pady=5)

# Загрузка данных и заполнение полей
saved_data = load_data()
populate_fields(saved_data)

# Кнопка для генерации CMR
generate_button = ttk.Button(root, text="Создать CMR", command=generate_cmr)
generate_button.grid(row=len(fields), column=0, columnspan=2, pady=20)

# Метка для отображения статуса
status_label = ttk.Label(root, text="")
status_label.grid(row=len(fields) + 1, column=0, columnspan=2, pady=10)

# Запуск главного цикла обработки событий
root.mainloop()
