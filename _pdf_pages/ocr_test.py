import easyocr
print('loading')
reader=easyocr.Reader(['ch_sim','en'], gpu=False, verbose=False)
print('reading')
res=reader.readtext(r'_pdf_pages\zhoushan_p01.png', detail=0, paragraph=True)
print('\n'.join(res[:40]))
