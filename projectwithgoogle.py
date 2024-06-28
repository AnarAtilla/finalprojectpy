import mysql.connector
import random
from tabulate import tabulate
import webbrowser

# Подключение к базе данных sakila
sakila_db = mysql.connector.connect(
    host="your_host",
    user="yor_id",
    password="your_password"
)

# Подключение к базе данных project_student
history_db = mysql.connector.connect(
    host="your_host",
    user="yor_id",
    password="your_password"
    database="project_student"
)

history_db.commit()


def save_search_query(search_text, sql_req):
    cursor = history_db.cursor()
    cursor.execute('''
    INSERT INTO search_history (search_text, SQL_req) VALUES (%s, %s)
    ''', (search_text, sql_req))
    history_db.commit()


def get_popular_queries():
    cursor = history_db.cursor()
    cursor.execute(
        "SELECT search_text, COUNT(*) as count FROM search_history GROUP BY "
        "search_text ORDER BY count DESC LIMIT 10")
    results = cursor.fetchall()

    genres = get_genres()
    formatted_results = []
    for search_text, count in results:
        if search_text is not None:
            parts = search_text.split(', ')
            if len(parts) == 3 and parts[1].isdigit():
                genre_index = int(parts[1]) - 1
                if 0 <= genre_index < len(genres):
                    parts[1] = genres[genre_index]
            formatted_results.append((', '.join(parts), count))
        else:
            formatted_results.append(("Пустой запрос", count))

    print(tabulate(formatted_results, headers=["Запрос", "Количество"], tablefmt="grid"))


def get_random_movies():
    cursor = sakila_db.cursor()
    cursor.execute("SELECT film_id FROM film")
    film_ids = [row[0] for row in cursor.fetchall()]
    random_film_ids = random.sample(film_ids, min(10, len(film_ids)))
    random_films = []
    for film_id in random_film_ids:
        cursor.execute("""
            SELECT f.title, f.release_year, c.name AS genre 
            FROM film f 
            JOIN film_category fc ON f.film_id = fc.film_id 
            JOIN category c ON fc.category_id = c.category_id 
            WHERE f.film_id = %s
        """, (film_id,))
        random_films.append(cursor.fetchone())
    return random_films


def get_genres():
    cursor = sakila_db.cursor()
    cursor.execute("SELECT name FROM category")
    genres = cursor.fetchall()
    return [genre[0] for genre in genres]


def search_by_criteria(keyword, genre, year):
    cursor = sakila_db.cursor()
    query = """
        SELECT DISTINCT f.title, f.release_year, c.name AS genre, f.description 
        FROM film f 
        JOIN film_category fc ON f.film_id = fc.film_id 
        JOIN category c ON fc.category_id = c.category_id 
        LEFT JOIN film_actor fa ON f.film_id = fa.film_id 
        LEFT JOIN actor a ON fa.actor_id = a.actor_id 
        WHERE 1=1
    """
    params = []

    if keyword != "*":
        query += " AND (f.title LIKE %s OR f.description LIKE %s OR a.first_name LIKE %s OR a.last_name LIKE %s)"
        params.extend([f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"])

    if genre != "*":
        genres = get_genres()
        if genre.isdigit() and 1 <= int(genre) <= len(genres):
            genre_name = genres[int(genre) - 1]
            query += " AND c.name = %s"
            params.append(genre_name)
        else:
            query += " AND c.name = %s"
            params.append(genre)

    if year != "*":
        query += " AND f.release_year = %s"
        params.append(year)

    query += " LIMIT 10"
    cursor.execute(query, params)
    return cursor.fetchall()


def main():
    print("ПОДБОРКА ФИЛЬМОВ:")
    random_movies = get_random_movies()
    print(tabulate(random_movies, headers=["Название", "Год", "Жанр"], tablefmt="grid"))

    print("\nЖАНРЫ:")
    genres = get_genres()
    half = len(genres) // 2
    for i in range(half):
        print(f"{i + 1}. {genres[i]:<20}{half + i + 1}. {genres[half + i]}")

    while True:
        print("\n1. Поиск: по ключевому слову, по ЖАНРУ, по году выпуска")
        print("2. Показать популярные запросы")
        print("3. Выход")
        choice = input("Выберите опцию: ")

        if choice == '1':
            search_criteria = input("Введите критерии поиска (например, Dark, 3, 2020 или *, 3, *): ").split(',')
            if len(search_criteria) != 3:
                print("Неверный формат ввода. Пожалуйста, введите три критерия через запятую.")
                continue

            keyword, genre, year = [criteria.strip() for criteria in search_criteria]

            results = search_by_criteria(keyword, genre, year)
            if results == [] and genre.isdigit():
                print("Неверный номер жанра. Пожалуйста, попробуйте снова.")
                continue

            if not results:
                print("Нет результатов по вашему запросу. Возвращаемся в меню.")
                continue

            search_text = f"Поиск: {keyword}, {genre}, {year}"
            sql_req = (
                f"SELECT DISTINCT f.title, f.release_year, c.name AS genre, f.description "
                f"FROM film f JOIN film_category fc ON f.film_id = fc.film_id "
                f"JOIN category c ON fc.category_id = c.category_id "
                f"LEFT JOIN film_actor fa ON f.film_id = fa.film_id "
                f"LEFT JOIN actor a ON fa.actor_id = a.actor_id WHERE 1=1"
            )
            if keyword != "*":
                sql_req += (
                    f" AND (f.title LIKE '%{keyword}%' OR f.description LIKE '%{keyword}%' "
                    f"OR a.first_name LIKE '%{keyword}%' OR a.last_name LIKE '%{keyword}%')"
                )
            if genre != "*":
                sql_req += f" AND c.name = '{genre}'"
            if year != "*":
                sql_req += f" AND f.release_year = '{year}'"
            sql_req += " LIMIT 10"
            save_search_query(search_text, sql_req)

            print("Результаты поиска:")
            for i, film in enumerate(results, 1):
                print(f"{i}. {film[0]} ({film[1]}) - {film[2]}")

            while True:
                try:
                    film_choice = int(input("Выберите фильм по номеру (0 для выхода): "))
                    if film_choice == 0:
                        break
                    selected_film = results[film_choice - 1]
                    watch_choice = input(f"Хотите посмотреть '{selected_film[0]} ({selected_film[1]})'? (yes/no): ").strip().lower()
                    if watch_choice == 'yes':
                        search_query = f"{selected_film[0]} {selected_film[1]} смотреть бесплатно"
                        search_url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}"
                        webbrowser.open(search_url)
                    break
                except (ValueError, IndexError):
                    print("Неверный номер. Пожалуйста, попробуйте снова.")

        elif choice == '2':
            print("Популярные запросы:")
            save_search_query("Показать популярные запросы",
                              "SELECT search_text, COUNT(*) as count FROM search_history GROUP BY search_text ORDER BY count DESC LIMIT 10")
            get_popular_queries()

        elif choice == '3':
            break

        else:
            print("Неверный выбор. Пожалуйста, попробуйте снова.")


if __name__ == "__main__":
    main()