from PyPDF2 import PdfReader

reader = PdfReader('71_a_ksiazka.pdf')
number_of_pages = len(reader.pages)
page = reader.pages[0]
text = page.extract_text()

full_text = []
for page in range(number_of_pages):
    page = reader.pages[page]
    text = page.extract_text()
    full_text.append(text)

text_str = ' '.join([elem for elem in full_text])

with open('sejm.txt', 'w') as f:
    f.writelines(text_str)

