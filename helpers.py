import requests

def make_books_from_likes(likes):
    books = []
     
    for like in likes:
        resp = requests.get(
            f"https://openlibrary.org/works/{like.book_key}.json",
            params={}
        )
        resp = resp.json()

        # make sure there is a description
        desc = resp.get("description", 'No description')
    
        if isinstance(desc, dict):
            desc = desc.get("value",'No description')

        # make sure there is a cover
        cover = resp.get("covers", ['No image available'])
        cover = cover[0]

        # make sure there is a published date
        published = resp.get("first_publish_date", 'No date available')

        authors = []

        for author in resp['authors']:
            authorResp = requests.get(
                f"https://openlibrary.org/{author['author']['key']}.json",
                params={}
            )

            authorResp = authorResp.json()

            authors.append(authorResp['name'])
            authors = list(set(authors ))
        

        book = {
            "title": resp['title'],
            "published": published,
            "description": desc,
            "authors" : authors,
            "cover" : cover,
            "key" : like.book_key
        }

        books.append(book)

    return books

