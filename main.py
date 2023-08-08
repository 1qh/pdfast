import os
from shutil import copyfileobj

from fastapi import Body, FastAPI, File, UploadFile

from bookmarks import BookmarksExtractor, PdfExtractor

app = FastAPI()


@app.post('/upload')
async def upload(file: UploadFile = File(...)):
    name = file.filename
    if name.endswith('.pdf'):
        os.makedirs('./uploaded', exist_ok=True)
        path = f'./uploaded/{name}'
        with open(path, 'wb') as f:
            copyfileobj(file.file, f)
        content = BookmarksExtractor(path)()
    elif name.endswith('.txt'):
        content = await file.read()
    return {
        'name': name,
        'content': content,
    }


@app.post('/edit')
async def edit(s: str = Body(...)):
    return [i.strip().split('\"')[1] for i in s.splitlines()]


@app.post('/extract')
async def extract(pdf: str, part: str, toc: str = Body(...)):
    return PdfExtractor(f'./uploaded/{pdf}', toc)(part)
