import tkinter as tk
from tkinter import ttk
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from pdfrw import PdfReader, PdfWriter, PageMerge
import io
# import time
# from datetime import datetime
import json
import os

DATA_FILE = "cmr_data.json"


def split_text(text, max_length):
    """Разбивает текст на строки с максимальной длиной max_length"""
    words = text.split(' ')
    lines = []
    current_line = ""

    for word in words:
        if len(current_line) + len(word) + 1 > max_length:
            lines.append(current_line)
            current_line = word
        else:
            if current_line:
                current_line += " " + word
            else:
                current_line = word

    if current_line:
        lines.append(current_line)

    return "\n".join(lines)


def draw_multiline_text(can, text, x, y, line_height):
    """Отрисовка многострочного текста на PDF"""
    lines = text.split('\n')
    for i, line in enumerate(lines):
        can.drawString(x, y - i * line_height, line)


def create_cmr_from_template(template_file, output_file, data):
    """Создание CMR накладной на основе шаблона"""
    template_pdf = PdfReader(template_file)
    text_filled_pdfs = []

    for page_num, template_page in enumerate(template_pdf.pages):
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=A4)

        can.setFont("Helvetica", 12)

        # Добавление многострочного текста
        draw_multiline_text(can, split_text(data["sender"], 30), 60, 742, 15)
        draw_multiline_text(can, split_text(data["receiver"], 30), 60, 675, 15)
        draw_multiline_text(can, split_text(data["carrier"], 20), 65, 105, 15)
        draw_multiline_text(can, split_text(data["place_of_loading"], 30), 60, 535, 15)
        draw_multiline_text(can, split_text(data["place_of_unloading"], 30), 60, 595, 15)
        draw_multiline_text(can, split_text(data["goods"], 40), 60, 430, 15)
        draw_multiline_text(can, split_text(data["weight"], 30), 435, 430, 15)
        draw_multiline_text(can, split_text(data["pieces"], 30), 100, 137, 15)
        draw_multiline_text(can, split_text(data["date_of_dispatch"], 30), 210, 137, 15)
        draw_multiline_text(can, split_text(data["vehicle_number"], 30), 370, 640, 15)

        # Добавление изображения с прозрачным фоном в двух местах
        img = ImageReader("stamp.png")
        can.drawImage(img, 430, 650, width=120, height=48, mask='auto')
        can.drawImage(img, 240, 75, width=120, height=48, mask='auto')

        can.showPage()
        can.save()

        packet.seek(0)
        text_filled_pdf = PdfReader(packet)
        text_filled_pdfs.append(text_filled_pdf.pages[0])

    for i, page in enumerate(template_pdf.pages):
        overlay_page = text_filled_pdfs[i]
        merged_page = PageMerge(page)
        merged_page.add(overlay_page).render()

    PdfWriter(output_file, trailer=template_pdf).write()


def save_data(data):
    """Сохранение введенных данных в файл"""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def load_data():
    """Загрузка данных из файла, если он существует"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def generate_cmr():
    """Генерация CMR накладной и сохранение введенных данных"""
    data = {
        "sender": sender_entry.get(),
        "receiver": receiver_entry.get(),
        "carrier": carrier_entry.get(),
        "place_of_loading": loading_entry.get(),
        "place_of_unloading": unloading_entry.get(),
        "goods": goods_entry.get(),
        "weight": weight_entry.get(),
        "pieces": pieces_entry.get(),
        "date_of_dispatch": date_entry.get(),
        "vehicle_number": vehicle_entry.get(),
    }

    save_data(data)

    template_file = "DokumentCMR.pdf"

    # Форматирование даты для использования в имени файла
    date_to_fileName = data["date_of_dispatch"]
    output_file = f"cmr_filled_{date_to_fileName}.pdf"

    #Создаём ЦМР
    create_cmr_from_template(template_file, output_file, data)

    # Сообщение о создании CMR и закрытие приложения через 5 секунд
    status_label.config(text="CMR накладная создана успешно!")
    root.after(500, root.destroy)


def populate_fields(data):
    """Заполнение полей формы данными"""
    sender_entry.insert(0, data.get("sender", "Sender"))
    receiver_entry.insert(0, data.get("receiver", "Receiver"))
    carrier_entry.insert(0, data.get("carrier", "Sender stamp"))
    loading_entry.insert(0, data.get("place_of_loading", "Loading place"))
    unloading_entry.insert(0, data.get("place_of_unloading", "Unloading place"))
    goods_entry.insert(0, data.get("goods", "Goods"))
    weight_entry.insert(0, data.get("weight", "Weight"))
    pieces_entry.insert(0, data.get("pieces", "City-sender"))
    date_entry.insert(0, data.get("date_of_dispatch", "dd-mm-yyyy"))
    vehicle_entry.insert(0, data.get("vehicle_number", "Truck / Trailer"))


# Создание главного окна
root = tk.Tk()
root.title("CMR Generator")

# Создание и размещение меток и полей ввода
ttk.Label(root, text="Отправитель").grid(row=0, column=0, padx=10, pady=5)
sender_entry = ttk.Entry(root, width=50)
sender_entry.grid(row=0, column=1, padx=10, pady=5)

ttk.Label(root, text="Получатель").grid(row=1, column=0, padx=10, pady=5)
receiver_entry = ttk.Entry(root, width=50)
receiver_entry.grid(row=1, column=1, padx=10, pady=5)

ttk.Label(root, text="Штамп отправителя").grid(row=2, column=0, padx=10, pady=5)
carrier_entry = ttk.Entry(root, width=50)
carrier_entry.grid(row=2, column=1, padx=10, pady=5)

ttk.Label(root, text="Место погрузки").grid(row=3, column=0, padx=10, pady=5)
loading_entry = ttk.Entry(root, width=50)
loading_entry.grid(row=3, column=1, padx=10, pady=5)

ttk.Label(root, text="Место выгрузки").grid(row=4, column=0, padx=10, pady=5)
unloading_entry = ttk.Entry(root, width=50)
unloading_entry.grid(row=4, column=1, padx=10, pady=5)

ttk.Label(root, text="Товары").grid(row=5, column=0, padx=10, pady=5)
goods_entry = ttk.Entry(root, width=50)
goods_entry.grid(row=5, column=1, padx=10, pady=5)

ttk.Label(root, text="Вес").grid(row=6, column=0, padx=10, pady=5)
weight_entry = ttk.Entry(root, width=50)
weight_entry.grid(row=6, column=1, padx=10, pady=5)

ttk.Label(root, text="Город отправитель").grid(row=7, column=0, padx=10, pady=5)
pieces_entry = ttk.Entry(root, width=50)
pieces_entry.grid(row=7, column=1, padx=10, pady=5)

ttk.Label(root, text="Дата отправки").grid(row=8, column=0, padx=10, pady=5)
date_entry = ttk.Entry(root, width=50)
date_entry.grid(row=8, column=1, padx=10, pady=5)

ttk.Label(root, text="Номер транспортного средства").grid(row=9, column=0, padx=10, pady=5)
vehicle_entry = ttk.Entry(root, width=50)
vehicle_entry.grid(row=9, column=1, padx=10, pady=5)

# Загрузка данных из файла и заполнение полей
saved_data = load_data()
populate_fields(saved_data)

# Создание и размещение кнопки для генерации CMR
generate_button = ttk.Button(root, text="Создать CMR", command=generate_cmr)
generate_button.grid(row=10, column=0, columnspan=2, pady=20)

# Создание и размещение метки для отображения статуса
status_label = ttk.Label(root, text="")
status_label.grid(row=11, column=0, columnspan=2, pady=10)

# Запуск главного цикла обработки событий
root.mainloop()
