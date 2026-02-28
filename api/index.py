from fastapi import FastAPI, Query
from .scraper import (
    scrape_home_categories,
    scrape_movie_detail,
    search,
    filter_by_genre,
    filter_by_year,
    filter_by_country
)

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Scraper API for shadowofthevampire.com"}

@app.get("/home")
def home_categories():
    return scrape_home_categories()

@app.get("/detail")
def movie_detail(url: str):
    return scrape_movie_detail(url)

@app.get("/search")
def search_movies(q: str = Query(..., description="Search query")):
    return search(q)

@app.get("/genre/{genre}")
def by_genre(genre: str):
    return filter_by_genre(genre)

@app.get("/year/{year}")
def by_year(year: str):
    return filter_by_year(year)

@app.get("/country/{country}")
def by_country(country: str):
    return filter_by_country(country)
