import base64

# Открываем изображение в бинарном режиме
with open("1.png", "rb") as image_file:
    # Читаем содержимое файла
    # Кодируем данные в base64
    image_data = base64.b64encode(image_file.read()).decode('utf-8')

# Записываем закодированные данные в текстовый файл
with open("1.txt", "w") as text_file:
    text_file.write(image_data)
